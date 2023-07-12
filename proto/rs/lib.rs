use time;
use slog;
use portus::ipc::Ipc;
use portus::lang::Scope;
use portus::{CongAlg, Datapath, DatapathInfo, DatapathTrait, Report};
use std::collections::HashMap;

// default value of time slot value, in terms of ms
pub const TIME_SLOT_INTERVAL_MSEC: u32 =  50;

/*
    RunCCP componement. (High level)
    -- ConAlg Trait(&self):	// override methods in the trait provided by CCP 
		-- impl fn datapath_programs(&self)
			1. Measuring: we mainly fetch ack and its RTT for sent packet.
			2. When to report measurement: set as our time interval
		-- impl fn new_flow(&self) -> Self:Flow
		    Create a new instance of MLCC instance for each new flow;
*/
pub struct RunCCP{
    pub logger: Option<slog::Logger>, // option means it must be Some() or None
    pub time_slot_interval: u32,
}

// Override ConAlg Trait provided by portus
impl<T: Ipc> CongAlg<T> for RunCCP{
    type Flow = MLCC<T>;

    fn name() -> &'static str {
        "mlcc"
    }

    // determine report variables
    fn datapath_programs(&self) -> HashMap<&'static str, String> {
        // time-slotted report, trigged every time slot 
        vec![
            (
                "default",
                String::from(
                    "
                (def
                    (Report 
                        (volatile inflight_pck 0)
                        (volatile inflight 0)
                        (volatile rtt 0)
                        (volatile botlw 0)
                        (volatile sendrate 0)
                    )
                    (time_slot_us 0)
                )
                (when true
                    (:= Report.inflight Flow.bytes_in_flight)
                    (:= Report.inflight_pck Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.botlw (max Report.botlw (/ Flow.bytes_in_flight Flow.rtt_sample_us)))
                    (:= Report.sendrate Flow.rate_outgoing)
                    (fallthrough)
                )
                (when (> Micros time_slot_us)
                    (report)
                    (:= Micros 0)
                )
            ",
                ),
            ), // first tuple
        ]
        .into_iter()
        .collect()
    }

    // DatapathInfo: info set passed by the datapath to CCP when a connection starts
    //      - id, ip, port... init_cwnd, mss
    // create a mlcc instance and return for new flow
    fn new_flow(&self, control: Datapath<T>, info: DatapathInfo) -> Self::Flow {
        let mut mlcc = MLCC{
            control_channel: control,
            sc: Scope::new(),
            logger: self.logger.clone(),
            rate_trans_ratio: 125_000, // 1 Mbps * ratio = DP rate (M bytes/us)
            mss: info.mss,
            time_slot_interval: self.time_slot_interval,
            start: time::now().to_timespec(),
            test_rate_flag: false,

            sock_id: info.sock_id,
            src_ip: info.src_ip,
            src_port: info.src_port,
            dst_ip: info.dst_ip,
            dst_port: info.dst_port,
        };

        // obtain basic information about new flow
        mlcc.logger.as_ref().map(|log| {
            slog::info!(log, "Successfully launch a new flow:";
                "dst_port" => info.dst_port,
                "dst_ip" => info.dst_ip,
                "src_port" => info.src_port,
                "src_ip" => info.src_ip,
                "sock_id" => info.sock_id,
            );
        });
        
        // Init sending rate with init-schedule
        mlcc.sc = mlcc.control_channel
                .set_program("default", Some(&[("Rate", 400 * mlcc.rate_trans_ratio), 
                    ("Cwnd", info.init_cwnd * 10),
                    ("time_slot_us", self.time_slot_interval*1000)]))
                .expect("Set default program failed for a new flow.");

        mlcc
    }
}

/*
    MLCC component. (Flow level)
    -- channel: Datapath
    -- [Settings] 			// flow sending related: sending rate/cwnd, etc.
    -- anonymous Trait(&self):
        -- impl a serius of operations to get measurement/update [Settings].
    --- Flow Trait(&self):
        -- impl fn on_report(&self), flow behavior
*/
pub struct MLCC<T: Ipc> {
    control_channel: Datapath<T>,
    sc: Scope,  // this store values of registers to be updated
    logger: Option<slog::Logger>,   // clone from runccp
    rate_trans_ratio: u32, 
    mss: u32,   // init with info.mss
    time_slot_interval: u32,
    start: time::Timespec, // start time of this flow
    test_rate_flag: bool,   // used for rate control test
    // datapath info
    sock_id: u32,
    src_ip: u32,
    src_port: u32,
    dst_ip: u32,
    dst_port: u32,
}


impl<T: Ipc> portus::Flow for MLCC<T> {
    // trigger by report recieved
    fn on_report(&mut self, _sock_id: u32, m: Report){
        // return if report is not for the current scope
        if self.sc.program_uid != m.program_uid {
            return;
        }
        
        // m.get_field("Report.botlw", &self.sc).unwrap() 
        self.logger.as_ref().map(|log| {
            slog::info!(log, "Report for on time slot";
                "rtt (us)" => m.get_field("Report.rtt", &self.sc).unwrap(),
                "inflight packets" => m.get_field("Report.inflight_pck", &self.sc).unwrap(),
                "inflight bytes" => m.get_field("Report.inflight", &self.sc).unwrap(),
                "dst_port" => self.dst_port,
                "dst_ip" => self.dst_ip,
                "src_port" => self.src_port,
                "src_ip" => self.src_ip,
                "sock_id" => self.sock_id,
            );
        });

        // test rate stablity
        if self.test_rate_flag {
            self.install_update(&[("Rate", 200 * self.rate_trans_ratio)]);
            self.test_rate_flag = false
        }
    }
}

impl<T: Ipc> MLCC<T> {
    // Update scope fields with erro processing
    fn install_update(&self, update: &[(&str, u32)]) {
        if let Err(e) = self.control_channel.update_field(&self.sc, update) {
            self.logger.as_ref().map(|log| {
                slog::warn!(log, "Cwnd and rate update error";
                      "err" => ?e,
                );
            });
        }
    }
}
