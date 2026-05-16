"""
CLI commands for automated bias detection and analysis.
"""

import cyclopts
from energybench.commands.analyse.bias import autodetect_bias_patterns
from energybench.commands.analyse.methods import compare_adjustment_methods

analyse_app = cyclopts.App(name="analyse", help="Automated bias detection and analysis tools")
analyse_app.command(name="autodetect-bias")(autodetect_bias_patterns)
analyse_app.command(name="compare-methods")(compare_adjustment_methods)
