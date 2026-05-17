from cyclopts import App
from energybench.cli.validate.summary import summary
from energybench.cli.validate.balance import daily_balance


validate_app = App(name="validate", help="Validate benchmarked outputs.")


validate_app.command(name="summary")(summary)
validate_app.command(name="daily-balance")(daily_balance)
