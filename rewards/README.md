# Balanced Smart Contracts

This is a repository holding the smart contracts layer of the balanced project. To deploy locally, we recommend setting up an instance of [T-Bears](https://www.icondev.io/docs/tbears-overview).

Oracles and price data for the synthetic assets are provided by [BAND](https://bandprotocol.com/).

In development, a day can be configured by the U_SECONDS_DAY param in each SCORE's constants file (consts.py). Dividing this by 24 makes daily actions occur every hour to speed testing.

The repository structure is:

- `core_contracts` - This folder holds all of the core smart contracts deployed for use in Balanced. It contains: 
  - `daofund` - Contract receiving Balanced tokens with use voted on by the DAO
  - `dex` - AMM Decentralized exchange with separate sICX/ICX queue instrument for trading minted assets
  - `dividends` - Contract used to pay out dividends to BALN token holders
  - `governance` - Used to vote on and perform DAO actions, as well as setting contract configuration variables
  - `loans` - Used to mint synthetic assets, collateralized by `sICX`
  - `oracle` - a dummy replacement for a BAND oracle, for use in development
  - `reserve` - reserve funds for risk situations
  - `rewards` - gives BALN tokens to addresses that earn them in platform actions
  - `staking` - manages SICX
- `token_contracts` - This folder holds all of the tokens used in the balanced protocol
  - `baln` - balanced token, used in platform governance and claiming dividends. Can be earned by contributing to or using balanced
  - `bnUSD` - Synthetic US Dollar, based on the band oracle price. Can be minted by locking up collateral (sICX)
  - `bwt` - Balanced worker token, given to core contributers as pay and earns a part of the inflation
  - `sicx` - staked ICX token, allows users to transact a staked token. Staking contract will allow choice of prep voted for in an update
