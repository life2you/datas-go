#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代币事件模型
处理代币事件数据的封装和验证
"""

class TokenEvent:
    """代币事件模型类"""
    
    def __init__(self, data):
        """
        初始化代币事件模型
        
        参数:
            data: 代币事件数据
        """
        self.data = data
    
    @property
    def signature(self):
        return self.data.get('signature')
    
    @property
    def mint(self):
        return self.data.get('mint')
    
    @property
    def trader_public_key(self):
        return self.data.get('traderPublicKey')
    
    @property
    def tx_type(self):
        return self.data.get('txType')
    
    @property
    def initial_buy(self):
        return self.data.get('initialBuy')
    
    @property
    def sol_amount(self):
        return self.data.get('solAmount')
    
    @property
    def bonding_curve_key(self):
        return self.data.get('bondingCurveKey')
    
    @property
    def v_tokens_in_bonding_curve(self):
        return self.data.get('vTokensInBondingCurve')
    
    @property
    def v_sol_in_bonding_curve(self):
        return self.data.get('vSolInBondingCurve')
    
    @property
    def market_cap_sol(self):
        return self.data.get('marketCapSol')
    
    @property
    def name(self):
        return self.data.get('name')
    
    @property
    def symbol(self):
        return self.data.get('symbol')
    
    @property
    def uri(self):
        return self.data.get('uri')
    
    @property
    def pool(self):
        return self.data.get('pool')
    
    def is_valid(self):
        """验证事件数据是否有效"""
        return self.signature is not None and self.mint is not None and self.tx_type is not None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'signature': self.signature,
            'mint': self.mint,
            'trader_public_key': self.trader_public_key,
            'tx_type': self.tx_type,
            'initial_buy': self.initial_buy,
            'sol_amount': self.sol_amount,
            'bonding_curve_key': self.bonding_curve_key,
            'v_tokens_in_bonding_curve': self.v_tokens_in_bonding_curve,
            'v_sol_in_bonding_curve': self.v_sol_in_bonding_curve,
            'market_cap_sol': self.market_cap_sol,
            'name': self.name,
            'symbol': self.symbol,
            'uri': self.uri,
            'pool': self.pool
        } 