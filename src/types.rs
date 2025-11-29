use num_bigint::BigInt;

use dtl_lexer::types::Variable;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Text {
    pub at: (usize, usize),
}

impl Text {
    pub fn new(at: (usize, usize)) -> Self {
        Self { at }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TranslatedText {
    pub at: (usize, usize),
}

impl TranslatedText {
    pub fn new(at: (usize, usize)) -> Self {
        Self { at }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum ArgumentType {
    Variable(Variable),
    ForVariable(ForVariable),
    Text(Text),
    TranslatedText(TranslatedText),
    Int(BigInt),
    Float(f64),
}

#[derive(Clone, Debug, PartialEq)]
pub struct Argument {
    pub at: (usize, usize),
    pub argument_type: ArgumentType,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ForVariableName {
    Counter,
    Counter0,
    RevCounter,
    RevCounter0,
    First,
    Last,
    Object,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ForVariable {
    pub variant: ForVariableName,
    pub parent_count: usize,
}
