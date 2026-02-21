"""Static analysis: control flow, data flow, symbol tables, taint analysis."""

from src.analysis.cfg import BasicBlock, ControlFlowGraph
from src.analysis.cfg_builder import CFGBuilder
from src.analysis.symbol_table import Symbol, Scope, SymbolTable
from src.analysis.data_flow import (
    Definition,
    Use,
    DataFlowAnalyzer,
    DataFlowResult,
)
from src.analysis.taint import (
    TaintSource,
    TaintSink,
    TaintSanitizer,
    TaintFlow,
    TaintAnalyzer,
)

__all__ = [
    "BasicBlock",
    "ControlFlowGraph",
    "CFGBuilder",
    "Symbol",
    "Scope",
    "SymbolTable",
    "Definition",
    "Use",
    "DataFlowAnalyzer",
    "DataFlowResult",
    "TaintSource",
    "TaintSink",
    "TaintSanitizer",
    "TaintFlow",
    "TaintAnalyzer",
]
