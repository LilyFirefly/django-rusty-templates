/// Custom `todo!` macro that returns a pickable `PyNotImplementedError` instead of
/// a non-pickable `PanicException`. This allows Django's test suite to run in parallel.
///
/// This macro shadows the standard library's `todo!` macro throughout the crate.
#[macro_export]
macro_rules! todo {
    () => {{
        let err: ::pyo3::PyErr = ::pyo3::exceptions::PyNotImplementedError::new_err("not yet implemented");
        return Err(err.into())
    }};
    ($($arg:tt)+) => {{
        let err: ::pyo3::PyErr = ::pyo3::exceptions::PyNotImplementedError::new_err(
            format!("not yet implemented: {}", format_args!($($arg)+))
        );
        return Err(err.into())
    }};
}

mod error;
mod filters;
mod loaders;
mod parse;
mod path;
pub mod render;
mod template;
mod types;
mod utils;
