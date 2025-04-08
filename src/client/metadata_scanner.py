#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代币元数据扫描器
定时扫描token表中未处理元数据的记录，获取并更新元数据
"""

import os
import sys
import time
import logging
import requests
import schedule
from datetime import datetime
import asyncio
from typing import Optional, Dict
from urllib.parse import urlparse
import aiohttp

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.db.database import Database
from src.core.config import HTTP_CONFIG

# 配置日志
logger = logging.getLogger(__name__)

class MetadataScanner:
    """代币元数据扫描器"""
    
    def __init__(self):
        self.db = Database()
        self.running = False
        self.scan_interval = 180  # 扫描间隔（秒）
        self.max_retries = 3
        self.retry_delay = 1  # 秒
    
    async def _run(self):
        """运行元数据扫描服务"""
        self.running = True
        while self.running:
            try:
                await self.scan_and_update()
            except Exception as e:
                logger.error(f"扫描元数据时发生错误: {str(e)}")
            await asyncio.sleep(self.scan_interval)
    
    async def scan_and_update(self):
        """扫描并更新代币元数据"""
        try:
            # 获取需要处理的代币列表
            query = """
            SELECT mint, uri FROM token 
            WHERE has_meta_data = 0 
            AND uri IS NOT NULL 
            LIMIT 100
            """
            cursor = self.db.execute(query)
            if not cursor:
                logger.error("获取代币列表失败")
                return
            
            tokens = cursor.fetchall()
            if not tokens:
                logger.info("没有需要处理的代币")
                return
            
            logger.info(f"开始处理 {len(tokens)} 个代币的元数据")
            
            for token in tokens:
                try:
                    await self._process_token_metadata(token)
                except Exception as e:
                    logger.error(f"处理代币 {token['mint']} 的元数据时发生错误: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"扫描元数据时发生错误: {str(e)}")
            raise
    
    async def _process_token_metadata(self, token):
        """处理单个代币的元数据"""
        mint = token['mint']
        uri = token['uri']
        
        logger.info(f"开始处理代币 {mint} 的元数据，URI: {uri}")
        
        # 验证URI格式
        if not self._validate_uri(uri):
            logger.warning(f"代币 {mint} 的URI格式无效: {uri}", exc_info=True)
            # 标记为已处理，避免重复处理无效URI
            self._update_token_metadata_status(mint)
            return
        
        # 获取元数据
        metadata = await self._fetch_metadata(uri)
        if not metadata:
            logger.warning(f"无法获取代币 {mint} 的元数据", exc_info=True)
            # 我们不标记为已处理，这样下次扫描还会重试
            return
        
        # 确保metadata是字典类型
        if not isinstance(metadata, dict):
            logger.error(f"代币 {mint} 的元数据不是有效的字典: {type(metadata)}", exc_info=True)
            return
        
        # 处理元数据格式，确保提取正确的字段
        processed_metadata = self._process_metadata_format(mint, metadata)
        
        # 保存元数据
        success = self._save_metadata(mint, processed_metadata)
        if success:
            # 更新代币状态
            self._update_token_metadata_status(mint)
        else:
            logger.error(f"保存代币 {mint} 的元数据失败", exc_info=True)
    
    def _validate_uri(self, uri: str) -> bool:
        """验证URI格式"""
        try:
            parsed = urlparse(uri)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    async def _fetch_metadata(self, uri: str) -> Optional[Dict]:
        """获取代币元数据"""
        for attempt in range(self.max_retries):
            try:
                # 检查URI
                if not uri or not isinstance(uri, str):
                    logger.error(f"无效的URI: {uri}", exc_info=True)
                    return None
                
                # 配置代理
                proxy = HTTP_CONFIG.get('proxy')
                proxy_auth = None
                if proxy:
                    proxy_auth = aiohttp.BasicAuth(
                        HTTP_CONFIG.get('proxy_username', ''),
                        HTTP_CONFIG.get('proxy_password', '')
                    )
                
                # 配置超时
                timeout = aiohttp.ClientTimeout(
                    total=30,  # 总超时时间
                    connect=10,  # 连接超时时间
                    sock_read=20  # 读取超时时间
                )
                
                # 配置请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                logger.debug(f"开始请求元数据URL: {uri}")
                
                async with aiohttp.ClientSession(
                    timeout=timeout,
                    headers=headers
                ) as session:
                    async with session.get(
                        uri,
                        proxy=proxy,
                        proxy_auth=proxy_auth,
                        ssl=False  # 禁用SSL验证
                    ) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                logger.debug(f"成功获取元数据内容: {uri}")
                                return data
                            except aiohttp.ContentTypeError as e:
                                logger.error(f"元数据内容解析失败，非JSON格式: {uri}, 错误: {str(e)}", exc_info=True)
                                # 尝试获取原始文本并手动解析
                                try:
                                    text = await response.text()
                                    logger.debug(f"获取到原始响应: {text[:200]}...")  # 只记录前200个字符避免日志过大
                                except Exception as text_err:
                                    logger.error(f"无法读取响应内容: {str(text_err)}", exc_info=True)
                                return None
                        else:
                            logger.warning(f"获取元数据失败，状态码: {response.status}, URL: {uri}")
                            try:
                                error_text = await response.text()
                                logger.debug(f"错误响应内容: {error_text[:200]}...")  # 只记录前200个字符
                            except Exception:
                                pass
            except aiohttp.ClientConnectorError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"连接错误，尝试重试 ({attempt + 1}/{self.max_retries}): {str(e)}, URL: {uri}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"连接元数据URL失败: {str(e)}, URL: {uri}", exc_info=True)
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"获取元数据失败，尝试重试 ({attempt + 1}/{self.max_retries}): {str(e)}, URL: {uri}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"获取元数据失败: {str(e)}, URL: {uri}", exc_info=True)
            except asyncio.TimeoutError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求超时，尝试重试 ({attempt + 1}/{self.max_retries}): {str(e)}, URL: {uri}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"请求元数据超时: {str(e)}, URL: {uri}", exc_info=True)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"获取元数据失败，尝试重试 ({attempt + 1}/{self.max_retries}): {str(e)}, URL: {uri}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"获取元数据失败: {str(e)}, URL: {uri}", exc_info=True)
        return None
    
    def _process_metadata_format(self, mint, metadata):
        """处理不同格式的元数据，统一格式"""
        try:
            # 创建一个标准化的元数据对象
            processed = {
                'description': None,
                'image': None,
                'twitter': None,
                'website': None
            }
            
            # 处理description字段
            if 'description' in metadata and metadata['description']:
                processed['description'] = str(metadata['description']).strip()
            
            # 处理image字段 - 可能在不同位置
            if 'image' in metadata and metadata['image']:
                processed['image'] = str(metadata['image']).strip()
            elif 'properties' in metadata and isinstance(metadata['properties'], dict):
                if 'files' in metadata['properties'] and isinstance(metadata['properties']['files'], list):
                    for file in metadata['properties']['files']:
                        if isinstance(file, dict) and 'uri' in file:
                            processed['image'] = str(file['uri']).strip()
                            break
            
            # 处理外部链接 - 可能在不同字段
            if 'external_url' in metadata and metadata['external_url']:
                processed['website'] = str(metadata['external_url']).strip()
            elif 'properties' in metadata and isinstance(metadata['properties'], dict):
                if 'external_url' in metadata['properties']:
                    processed['website'] = str(metadata['properties']['external_url']).strip()
            
            # 处理社交媒体链接 - 通常在外部链接或属性中
            if 'properties' in metadata and isinstance(metadata['properties'], dict):
                # 查找Twitter链接
                if 'twitter_url' in metadata['properties']:
                    processed['twitter'] = str(metadata['properties']['twitter_url']).strip()
                
            # 如果社交链接在links字段中
            if 'links' in metadata and isinstance(metadata['links'], dict):
                if 'twitter' in metadata['links']:
                    processed['twitter'] = str(metadata['links']['twitter']).strip()
            
            # 记录处理后的元数据
            logger.debug(f"处理后的元数据: {processed}")
            
            return processed
        except Exception as e:
            logger.error(f"处理代币 {mint} 的元数据格式时发生错误: {str(e)}", exc_info=True)
            # 返回原始元数据，确保处理继续
            return metadata
    
    def _save_metadata(self, mint: str, metadata: Dict) -> bool:
        """保存代币元数据"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                # 检查token_metadata表是否存在
                check_table_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'token_metadata'
                )
                """
                cursor = self.db.execute(check_table_query)
                if not cursor:
                    logger.error("检查token_metadata表是否存在失败", exc_info=True)
                    return False
                    
                table_exists = cursor.fetchone()['exists']
                
                # 如果表不存在，创建表
                if not table_exists:
                    logger.info("token_metadata表不存在，准备创建")
                    create_table_query = """
                    CREATE TABLE IF NOT EXISTS token_metadata (
                        id SERIAL PRIMARY KEY,
                        mint VARCHAR(255) NOT NULL UNIQUE,
                        description TEXT,
                        image VARCHAR(1024),
                        twitter VARCHAR(1024),
                        website VARCHAR(1024),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_token_metadata_mint ON token_metadata(mint);
                    """
                    self.db.execute(create_table_query)
                    logger.info("成功创建token_metadata表")
                
                # 获取description, image, twitter, website的列最大长度
                get_columns_info = """
                SELECT 
                    column_name, 
                    character_maximum_length
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = 'public' 
                    AND table_name = 'token_metadata'
                    AND column_name IN ('description', 'image', 'twitter', 'website');
                """
                cursor = self.db.execute(get_columns_info)
                column_lengths = {}
                
                if cursor:
                    for row in cursor.fetchall():
                        column_lengths[row['column_name']] = row['character_maximum_length']
                
                # 准备数据，确保不超过列的最大长度
                description = metadata.get('description')
                image = metadata.get('image')
                twitter = metadata.get('twitter')
                website = metadata.get('website')
                
                # 如果是TEXT类型，那么character_maximum_length是None，不需要截断
                # 否则根据最大长度截断
                if 'description' in column_lengths and column_lengths['description'] is not None:
                    if description and len(description) > column_lengths['description']:
                        description = description[:column_lengths['description']]
                        logger.warning(f"代币 {mint} 的描述被截断至 {column_lengths['description']} 个字符")
                
                if 'image' in column_lengths and column_lengths['image'] is not None:
                    if image and len(image) > column_lengths['image']:
                        image = image[:column_lengths['image']]
                        logger.warning(f"代币 {mint} 的图片URL被截断至 {column_lengths['image']} 个字符")
                
                if 'twitter' in column_lengths and column_lengths['twitter'] is not None:
                    if twitter and len(twitter) > column_lengths['twitter']:
                        twitter = twitter[:column_lengths['twitter']]
                        logger.warning(f"代币 {mint} 的Twitter URL被截断至 {column_lengths['twitter']} 个字符")
                
                if 'website' in column_lengths and column_lengths['website'] is not None:
                    if website and len(website) > column_lengths['website']:
                        website = website[:column_lengths['website']]
                        logger.warning(f"代币 {mint} 的网站URL被截断至 {column_lengths['website']} 个字符")
                
                query = """
                INSERT INTO token_metadata (
                    mint, description, image, twitter, website
                ) VALUES (
                    %(mint)s, %(description)s, %(image)s, %(twitter)s, %(website)s
                ) ON CONFLICT (mint) DO UPDATE SET
                    description = EXCLUDED.description,
                    image = EXCLUDED.image,
                    twitter = EXCLUDED.twitter,
                    website = EXCLUDED.website,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
                """
                
                data = {
                    'mint': mint,
                    'description': description,
                    'image': image,
                    'twitter': twitter,
                    'website': website
                }
                
                # 记录详细的调试信息
                logger.debug(f"保存元数据，参数: {data}")
                
                cursor = self.db.execute(query, data)
                if cursor:
                    result = cursor.fetchone()
                    if result and 'id' in result:
                        logger.info(f"代币 {mint} 的元数据已保存")
                        return True
                    else:
                        if attempt < max_retries - 1:
                            logger.warning(f"保存代币 {mint} 的元数据失败：未返回ID，尝试重试 ({attempt + 1}/{max_retries})", exc_info=True)
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"保存代币 {mint} 的元数据失败：未返回ID，已达到最大重试次数", exc_info=True)
                            return False
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"保存代币 {mint} 的元数据失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}", exc_info=True)
                    time.sleep(retry_delay)
                else:
                    logger.error(f"保存代币 {mint} 的元数据失败: {str(e)}", exc_info=True)
                    return False
    
    def _update_token_metadata_status(self, mint: str):
        """更新代币的元数据状态"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                query = """
                UPDATE token 
                SET has_meta_data = 1 
                WHERE mint = %s
                """
                cursor = self.db.execute(query, (mint,))
                if cursor and cursor.rowcount > 0:
                    logger.info(f"代币 {mint} 的元数据状态已更新")
                    return True
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"更新代币 {mint} 的元数据状态失败，尝试重试 ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.warning(f"更新代币 {mint} 的元数据状态失败，已达到最大重试次数")
                        return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"更新代币 {mint} 的元数据状态失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"更新代币 {mint} 的元数据状态失败: {str(e)}")
                    return False


def run_scanner():
    """运行元数据扫描器"""
    scanner = MetadataScanner()
    
    # 定义扫描任务
    async def scan_task():
        await scanner.scan_and_update()
    
    # 设置定时任务，每3分钟执行一次
    schedule.every(3).minutes.do(scan_task)
    
    # 首次立即执行一次
    asyncio.run(scan_task())
    
    # 持续运行定时任务
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scanner() 