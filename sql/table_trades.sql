CREATE TABLE "public"."token_trade" (
  "id" int4 NOT NULL DEFAULT nextval('token_trade_id_seq'::regclass),
  "signature" text COLLATE "pg_catalog"."default" NOT NULL,
  "mint" text COLLATE "pg_catalog"."default" NOT NULL,
  "trader_public_key" text COLLATE "pg_catalog"."default" NOT NULL,
  "tx_type" text COLLATE "pg_catalog"."default" NOT NULL,
  "token_amount" numeric(20,6),
  "sol_amount" numeric(20,9),
  "new_token_balance" numeric(20,6),
  "bonding_curve_key" text COLLATE "pg_catalog"."default",
  "v_tokens_in_bonding_curve" numeric(20,6),
  "v_sol_in_bonding_curve" numeric(20,9),
  "market_cap_sol" numeric(20,9),
  "pool" text COLLATE "pg_catalog"."default",
  "trade_time" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "token_trade_pkey" PRIMARY KEY ("id")
)
;

ALTER TABLE "public"."token_trade" 
  OWNER TO "postgres";

CREATE INDEX "idx_token_trade_mint" ON "public"."token_trade" USING btree (
  "mint" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_trade_time" ON "public"."token_trade" USING btree (
  "trade_time" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_trade_trader" ON "public"."token_trade" USING btree (
  "trader_public_key" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_trade_type" ON "public"."token_trade" USING btree (
  "tx_type" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

COMMENT ON COLUMN "public"."token_trade"."signature" IS '交易签名';

COMMENT ON COLUMN "public"."token_trade"."mint" IS '代币mint地址';

COMMENT ON COLUMN "public"."token_trade"."trader_public_key" IS '交易者的公钥';

COMMENT ON COLUMN "public"."token_trade"."tx_type" IS '交易类型(buy/sell)';

COMMENT ON COLUMN "public"."token_trade"."token_amount" IS '交易的代币数量';

COMMENT ON COLUMN "public"."token_trade"."sol_amount" IS '交易的SOL数量';

COMMENT ON COLUMN "public"."token_trade"."new_token_balance" IS '交易后的代币余额';

COMMENT ON COLUMN "public"."token_trade"."bonding_curve_key" IS '绑定曲线键';

COMMENT ON COLUMN "public"."token_trade"."v_tokens_in_bonding_curve" IS '绑定曲线中的代币数量';

COMMENT ON COLUMN "public"."token_trade"."v_sol_in_bonding_curve" IS '绑定曲线中的SOL数量';

COMMENT ON COLUMN "public"."token_trade"."market_cap_sol" IS '以SOL计算的市值';

COMMENT ON COLUMN "public"."token_trade"."pool" IS '所属交易池';

COMMENT ON COLUMN "public"."token_trade"."trade_time" IS '交易时间';

COMMENT ON TABLE "public"."token_trade" IS '存储代币交易记录的表';