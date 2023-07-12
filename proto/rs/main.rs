// use lib.rs
mod lib;
use lib::RunCCP;

use slog;
use clap;
use portus;

/* 
    Receive arguments:
        --ipc: netlink/unix, default netlink
        --time_slot_interval: (ms), fefault 10000ms
    Return:
        (rccp: RunCCP{log, time_slot_interval}, ipc: String)
*/
fn make_args(log: slog::Logger) -> Result<(RunCCP, String), String> {
    let time_slot_interval_default = format!("{}", lib::TIME_SLOT_INTERVAL_MSEC);
    let matches = clap::App::new("Run CCP Program")
        .version("0.2.2")
        .author("xyzhao <xyzhao@cs.hku.hk>")
        .about("Implementation of MLCC on CCP")
        .arg(clap::Arg::with_name("ipc")
            .long("ipc")
            .help("Sets the type of ipc to use: (netlink|unix)")
            .default_value("netlink")
            .validator(portus::algs::ipc_valid))
        .arg(clap::Arg::with_name("time_slot_interval")
            .long("time_slot_interval")
            .help("Set the time slot value in (ms)")
            .default_value(&time_slot_interval_default))
        .get_matches();
    
    let time_slot_interval_arg = time::Duration::milliseconds(
        i64::from_str_radix(matches.value_of("time_slot_interval").unwrap(), 10) // 10进制
            .map_err(|e| format!("{:?}", e))
            .and_then(|time_slot_interval_arg| {
                if time_slot_interval_arg <= 0 {
                    Err(format!(
                        "time_slot_interval must be positive: {}",
                        time_slot_interval_arg
                    ))
                } else {
                    Ok(time_slot_interval_arg)
                }
            })?,
    );

    let time_slot_interval_arg = u32::from_str_radix(matches.value_of("time_slot_interval").unwrap(), 10);
    slog::info!(log, "Successfully receive arguments for RunCCP.");

    Ok((
        RunCCP {
            logger: Some(log),
            time_slot_interval: time_slot_interval_arg.unwrap(),
        },
        String::from(matches.value_of("ipc").unwrap()),
    ))
}

/*
    Main function:
        init an RunCCP instance with args and start.
*/
fn main(){
    let log = portus::algs::make_logger();
    let (rccp, ipc) = make_args(log.clone())
        .map_err(|e| slog::warn!(log, "bad argument"; "err" => ?e))
        .unwrap();

    slog::info!(log, "Configured RunCCP"; 
        "ipc" => ipc.clone(),
        "time_slot_interval(ms)" => ?rccp.time_slot_interval,
    );

    portus::start!(ipc.as_str(), Some(log), rccp).expect("Fail to launch portus::start.");
}
