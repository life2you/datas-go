CREATE TABLE "public"."token" (
  "id" int4 NOT NULL DEFAULT nextval('token_id_seq'::regclass),
  "signature" text COLLATE "pg_catalog"."default" NOT NULL,
  "mint" text COLLATE "pg_catalog"."default" NOT NULL,
  "trader_public_key" text COLLATE "pg_catalog"."default" NOT NULL,
  "initial_buy" numeric(20,6),
  "sol_amount" numeric(20,9),
  "bonding_curve_key" text COLLATE "pg_catalog"."default",
  "v_tokens_in_bonding_curve" numeric(20,6),
  "v_sol_in_bonding_curve" numeric(20,9),
  "market_cap_sol" numeric(20,9),
  "name" text COLLATE "pg_catalog"."default",
  "symbol" text COLLATE "pg_catalog"."default",
  "uri" text COLLATE "pg_catalog"."default",
  "pool" text COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "latest_usd_price" numeric(24,12),
  "has_meta_data" int2 DEFAULT 0,
  CONSTRAINT "token_pkey" PRIMARY KEY ("id")
)
;

ALTER TABLE "public"."token" 
  OWNER TO "postgres";

CREATE INDEX "idx_token_mint" ON "public"."token" USING btree (
  "mint" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_pool" ON "public"."token" USING btree (
  "pool" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_trader" ON "public"."token" USING btree (
  "trader_public_key" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_usd_price" ON "public"."token" USING btree (
  "latest_usd_price" "pg_catalog"."numeric_ops" ASC NULLS LAST
);

COMMENT ON COLUMN "public"."token"."signature" IS '交易签名';

COMMENT ON COLUMN "public"."token"."mint" IS '代币mint地址';

COMMENT ON COLUMN "public"."token"."trader_public_key" IS '交易者的公钥';

COMMENT ON COLUMN "public"."token"."initial_buy" IS '初始购买的代币数量';

COMMENT ON COLUMN "public"."token"."sol_amount" IS '交易的SOL数量';

COMMENT ON COLUMN "public"."token"."bonding_curve_key" IS '绑定曲线键';

COMMENT ON COLUMN "public"."token"."v_tokens_in_bonding_curve" IS '绑定曲线中的代币数量';

COMMENT ON COLUMN "public"."token"."v_sol_in_bonding_curve" IS '绑定曲线中的SOL数量';

COMMENT ON COLUMN "public"."token"."market_cap_sol" IS '以SOL计算的市值';

COMMENT ON COLUMN "public"."token"."name" IS '代币名称';

COMMENT ON COLUMN "public"."token"."symbol" IS '代币符号';

COMMENT ON COLUMN "public"."token"."uri" IS '代币元数据URI';

COMMENT ON COLUMN "public"."token"."pool" IS '所属交易池';

COMMENT ON COLUMN "public"."token"."created_at" IS '记录创建时间';

COMMENT ON COLUMN "public"."token"."latest_usd_price" IS '代币最新美元价格';

COMMENT ON TABLE "public"."token" IS '存储代币创建和交易事件的表';