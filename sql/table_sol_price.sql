-- SOL价格历史记录表
-- 用于存储SOL/USD价格的历史数据
CREATE TABLE IF NOT EXISTS sol_price (
    id SERIAL PRIMARY KEY,                       -- 自增主键
    price NUMERIC(16, 6) NOT NULL,               -- SOL价格，单位USD
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- 记录时间，默认为当前时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() -- 记录创建时间
);

-- 创建时间索引，加速时间范围查询
CREATE INDEX IF NOT EXISTS idx_sol_price_timestamp ON sol_price (timestamp);

-- 添加注释
COMMENT ON TABLE sol_price IS 'SOL/USD价格历史记录';
COMMENT ON COLUMN sol_price.id IS '记录ID';
COMMENT ON COLUMN sol_price.price IS 'SOL的美元价格';
COMMENT ON COLUMN sol_price.timestamp IS '价格记录时间';
COMMENT ON COLUMN sol_price.created_at IS '数据入库时间'; 