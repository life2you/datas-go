CREATE TABLE "public"."token_metadata" (
  "id" int4 NOT NULL DEFAULT nextval('token_metadata_id_seq'::regclass),
  "mint" varchar(44) COLLATE "pg_catalog"."default" NOT NULL,
  "description" text COLLATE "pg_catalog"."default",
  "image" varchar(255) COLLATE "pg_catalog"."default",
  "twitter" varchar(255) COLLATE "pg_catalog"."default",
  "website" varchar(255) COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) DEFAULT now(),
  "updated_at" timestamp(6) DEFAULT now(),
  CONSTRAINT "token_metadata_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "token_metadata_mint_key" UNIQUE ("mint")
)
;

ALTER TABLE "public"."token_metadata" 
  OWNER TO "postgres";

CREATE INDEX "idx_token_metadata_mint" ON "public"."token_metadata" USING btree (
  "mint" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

COMMENT ON COLUMN "public"."token_metadata"."mint" IS '代币mint地址，关联到token表';

COMMENT ON COLUMN "public"."token_metadata"."description" IS '代币描述信息';

COMMENT ON COLUMN "public"."token_metadata"."image" IS '代币图片链接';

COMMENT ON COLUMN "public"."token_metadata"."twitter" IS '代币Twitter链接';

COMMENT ON COLUMN "public"."token_metadata"."website" IS '代币官方网站链接';

COMMENT ON COLUMN "public"."token_metadata"."created_at" IS '记录创建时间';

COMMENT ON COLUMN "public"."token_metadata"."updated_at" IS '记录更新时间';

COMMENT ON TABLE "public"."token_metadata" IS '存储代币元数据信息的表';