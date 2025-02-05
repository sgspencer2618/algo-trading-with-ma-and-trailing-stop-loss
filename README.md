# Dynamic Algorithmic Trading Strategy Utilizing Moving Average Crosses and Trailing Stop-Loss

This algorithmic trading strategy was developed in preparation for the algorithmic trading portion of the *Rotman Commerce Fintech Association Challenge (RCFTAC)* in January of 2025 (Unfortunately, due to academic scheduling conflicts, I was unable to attend the competition day). The strategy combines **moving average crosses** with a **trailing stop-loss** to maximize profits in a real-time trading environment, simulated by the **BMO Financial Group Finance Research and Trading Lab**, and using the RIT (Rotman Interactive Trader) software as the API endpoint for the python code. The code showcases:

- Reactive action to real-time market changes and execution of trades based on API data.
- An algorithmic implementation of moving average cross cues (Golden crosses, Death crosses).
- The result of iterative development of an algorithmic trading strategy, performing successfully in numerous trial runs.

Moving average crosses and trailing stop-loss were settled on as stratagems through process of trial-and-error, with moving averages alone generating rational signals – however yeilding concerning losses, and trailing stop-loss helping to mitigate the issue of excessive loss. The algorithm code was built off of a base script file that was provided by the organizers (available at the starter page linked in the credits) containing only basic functions such as getter and setter methods for ticks and bid-ask spreads.

# Market Dynamics and Results
Below were the market dynamics (sourced from the competition starter page linked in the credits):
Ticker |	OWL |	CROW	| DOVE	| DUCK
-------|------|-------|-------|------
Type |	Stock |	Stock |	Stock |	Stock
Starting Price |	High |	High |	Low	| Medium
Volatility |	Low	| Medium |	High |	Medium
Fee/share (Market Orders) |	0.03 |	-0.02 |	-0.03 |	0.02
Rebate/share (Limit Orders)	| 0.04	| -0.03	| -0.04	| 0.03
Max Order Size	| 5000	| 5000	| 5000	| 5000
Gross/Net Limits	| 250000	| 250000	| 250000	| 250000

With the following heat specifications:

- Trading time per heat: 600 seconds (10 minutes)
- Calendar time per heat: one month of trading

The algorithm realized a P&L of **177,220.17** without incurring any fines (due to exceeding trading/position limits, etc.). A table summary and P&L graph are displayed below from one of the practice heats that were run leading up to the event:

![image](https://github.com/user-attachments/assets/d54ff6cc-dc5f-4843-8e33-be54ee87e7e5)

![image](https://github.com/user-attachments/assets/74793c6e-56fb-497d-b47e-1f9cab6a5808)

The chart below graphs the positions taken by the algorithm on each stock throughout the heat's duration.

![image](https://github.com/user-attachments/assets/62090406-ef6e-4971-b46e-6ffb8294e7d3)

As can be seen from the graphs above, the algorithm was profitable for the majority of the heat, with little to no human intervention throughout its duration.

# Credits

Case starter page: https://inside.rotman.utoronto.ca/financelab/cases/algorithmic-market-making-case-v1-2/ Copyright © Rotman School of Management, University of Toronto | BMO Financial Group Finance Research and Trading Lab
