-- 创建存储交易记录的表
CREATE TABLE token_trade (
    id SERIAL PRIMARY KEY,
    signature TEXT NOT NULL,
    mint TEXT NOT NULL,
    trader_public_key TEXT NOT NULL,
    tx_type TEXT NOT NULL,
    token_amount NUMERIC(20, 6),
    sol_amount NUMERIC(20, 9),
    new_token_balance NUMERIC(20, 6),
    bonding_curve_key TEXT,
    v_tokens_in_bonding_curve NUMERIC(20, 6),
    v_sol_in_bonding_curve NUMERIC(20, 9),
    market_cap_sol NUMERIC(20, 9),
    pool TEXT,
    trade_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加索引以提高查询性能
CREATE INDEX idx_token_trade_mint ON token_trade(mint);
CREATE INDEX idx_token_trade_trader ON token_trade(trader_public_key);
CREATE INDEX idx_token_trade_type ON token_trade(tx_type);
CREATE INDEX idx_token_trade_time ON token_trade(trade_time);

-- 添加注释
COMMENT ON TABLE token_trade IS '存储代币交易记录的表';
COMMENT ON COLUMN token_trade.signature IS '交易签名';
COMMENT ON COLUMN token_trade.mint IS '代币mint地址';
COMMENT ON COLUMN token_trade.trader_public_key IS '交易者的公钥';
COMMENT ON COLUMN token_trade.tx_type IS '交易类型(buy/sell)';
COMMENT ON COLUMN token_trade.token_amount IS '交易的代币数量';
COMMENT ON COLUMN token_trade.sol_amount IS '交易的SOL数量';
COMMENT ON COLUMN token_trade.new_token_balance IS '交易后的代币余额';
COMMENT ON COLUMN token_trade.bonding_curve_key IS '绑定曲线键';
COMMENT ON COLUMN token_trade.v_tokens_in_bonding_curve IS '绑定曲线中的代币数量';
COMMENT ON COLUMN token_trade.v_sol_in_bonding_curve IS '绑定曲线中的SOL数量';
COMMENT ON COLUMN token_trade.market_cap_sol IS '以SOL计算的市值';
COMMENT ON COLUMN token_trade.pool IS '所属交易池';
COMMENT ON COLUMN token_trade.trade_time IS '交易时间'; 