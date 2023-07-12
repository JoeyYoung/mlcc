from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name='generic_cong_avoid',
    version='2.0',
    rust_extensions=[RustExtension(
        'generic_cong_avoid',
        'Cargo.toml',
        binding=Binding.PyO3
    )],
    packages=['generic_cong_avoid'],
    license='MIT',
    zip_safe=False
)
