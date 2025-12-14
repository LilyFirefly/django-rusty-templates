#![expect(unused_assignments)]
use std::borrow::Cow;
use std::path::{Path, PathBuf};

use miette::{Diagnostic, SourceSpan};
use sugar_path::SugarPath;
use thiserror::Error;

use dtl_lexer::types::At;

#[derive(Error, Debug, Diagnostic, PartialEq, Eq)]
pub enum RelativePathError {
    #[error(
        "The relative path {template_path} points outside the file hierarchy that template '{origin}' is in."
    )]
    Outside {
        #[label("relative path")]
        at: SourceSpan,
        origin: PathBuf,
        template_path: String,
    },
    #[error("The relative path {path} cannot be evaluated due to an unknown template origin.")]
    UnknownOrigin {
        path: String,
        #[label("here")]
        at: SourceSpan,
    },
}

pub fn construct_relative_path<'a>(
    path: &'a str,
    origin: Option<&'a str>,
    at: At,
) -> Result<Option<Cow<'a, str>>, RelativePathError> {
    let adjacent = path.starts_with("./");
    if !adjacent && !path.starts_with("../") {
        return Ok(None);
    }
    match origin {
        Some(origin) => {
            let origin = Path::new(origin);
            let path = match origin.parent() {
                None if adjacent => Path::new(path).normalize(),
                None => {
                    return Err(RelativePathError::Outside {
                        at: at.into(),
                        origin: origin.to_path_buf(),
                        template_path: path.to_string(),
                    });
                }
                Some(directory) => {
                    let new_path = Path::join(directory, path).normalize();
                    if new_path.starts_with("../") {
                        return Err(RelativePathError::Outside {
                            at: at.into(),
                            origin: origin.to_path_buf(),
                            template_path: path.to_string(),
                        });
                    }
                    new_path
                }
            };
            Ok(Some(Cow::Owned(
                path.to_str()
                    .expect("Template names should be valid unicode.")
                    .to_string(),
            )))
        }
        None => Err(RelativePathError::UnknownOrigin {
            at: at.into(),
            path: path.to_string(),
        }),
    }
}
