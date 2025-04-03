CREATE TABLE "public"."token_replies" (
  "id" int4 NOT NULL DEFAULT nextval('token_replies_id_seq'::regclass),
  "mint" text COLLATE "pg_catalog"."default" NOT NULL,
  "is_buy" bool,
  "sol_amount" numeric(20,9),
  "user_address" text COLLATE "pg_catalog"."default" NOT NULL,
  "timestamp" int8 NOT NULL,
  "datetime" timestamp(6),
  "text" text COLLATE "pg_catalog"."default",
  "username" text COLLATE "pg_catalog"."default",
  "total_likes" int4,
  "created_at" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "token_replies_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "token_replies_mint_user_address_timestamp_key" UNIQUE ("mint", "user_address", "timestamp")
)
;

ALTER TABLE "public"."token_replies" 
  OWNER TO "postgres";

CREATE INDEX "idx_token_replies_datetime" ON "public"."token_replies" USING btree (
  "datetime" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_replies_mint" ON "public"."token_replies" USING btree (
  "mint" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_replies_timestamp" ON "public"."token_replies" USING btree (
  "timestamp" "pg_catalog"."int8_ops" ASC NULLS LAST
);

CREATE INDEX "idx_token_replies_user" ON "public"."token_replies" USING btree (
  "user_address" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);