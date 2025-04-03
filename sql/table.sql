-- 创建存储代币的表
CREATE TABLE token (
    id SERIAL PRIMARY KEY,
    signature TEXT NOT NULL,
    mint TEXT NOT NULL,
    trader_public_key TEXT NOT NULL,
    initial_buy NUMERIC(20, 6),
    sol_amount NUMERIC(20, 9),
    bonding_curve_key TEXT,
    v_tokens_in_bonding_curve NUMERIC(20, 6),
    v_sol_in_bonding_curve NUMERIC(20, 9),
    market_cap_sol NUMERIC(20, 9),
    name TEXT,
    symbol TEXT,
    uri TEXT,
    pool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加索引以提高查询性能
CREATE INDEX idx_token_mint ON token(mint);
CREATE INDEX idx_token_trader ON token(trader_public_key);
CREATE INDEX idx_token_pool ON token(pool);

-- 添加注释
COMMENT ON TABLE token IS '存储代币创建和交易事件的表';
COMMENT ON COLUMN token.signature IS '交易签名';
COMMENT ON COLUMN token.mint IS '代币mint地址';
COMMENT ON COLUMN token.trader_public_key IS '交易者的公钥';
COMMENT ON COLUMN token.initial_buy IS '初始购买的代币数量';
COMMENT ON COLUMN token.sol_amount IS '交易的SOL数量';
COMMENT ON COLUMN token.bonding_curve_key IS '绑定曲线键';
COMMENT ON COLUMN token.v_tokens_in_bonding_curve IS '绑定曲线中的代币数量';
COMMENT ON COLUMN token.v_sol_in_bonding_curve IS '绑定曲线中的SOL数量';
COMMENT ON COLUMN token.market_cap_sol IS '以SOL计算的市值';
COMMENT ON COLUMN token.name IS '代币名称';
COMMENT ON COLUMN token.symbol IS '代币符号';
COMMENT ON COLUMN token.uri IS '代币元数据URI';
COMMENT ON COLUMN token.pool IS '所属交易池';
COMMENT ON COLUMN token.created_at IS '记录创建时间'; 