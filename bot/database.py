#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()


class SessionStatus(enum.Enum):
    """Session 状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WithdrawalStatus(enum.Enum):
    """提现状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100))
    balance = Column(Float, default=0.0)
    trc20_address = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, balance={self.balance})>"


class Session(Base):
    """Session 表"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    phone = Column(String(20), nullable=False)
    country_code = Column(String(10), nullable=False)
    session_file = Column(String(200), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewer_id = Column(Integer)
    reject_reason = Column(String(200))
    
    def __repr__(self):
        return f"<Session(id={self.id}, phone={self.phone}, status={self.status.value})>"


class Price(Base):
    """价格表"""
    __tablename__ = 'prices'
    
    country_code = Column(String(10), primary_key=True)
    country_name = Column(String(100), nullable=False)
    flag_emoji = Column(String(10))
    price = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Price(country_code={self.country_code}, price={self.price})>"


class Withdrawal(Base):
    """提现表"""
    __tablename__ = 'withdrawals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    trc20_address = Column(String(100), nullable=False)
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    admin_id = Column(Integer)
    
    def __repr__(self):
        return f"<Withdrawal(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status.value})>"


class Database:
    """数据库管理类"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def create_user(self, user_id: int, username: str = None):
        """创建用户"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(user_id=user_id, username=username)
                session.add(user)
                session.commit()
            return user
        finally:
            session.close()
    
    def get_user(self, user_id: int):
        """获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(user_id=user_id).first()
        finally:
            session.close()
    
    def update_balance(self, user_id: int, amount: float):
        """更新余额"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.balance += amount
                session.commit()
                return user.balance
        finally:
            session.close()
    
    def set_trc20_address(self, user_id: int, address: str):
        """设置 TRC20 地址"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.trc20_address = address
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def create_session_record(self, user_id: int, phone: str, country_code: str, 
                             session_file: str, price: float):
        """创建 Session 记录"""
        session = self.get_session()
        try:
            record = Session(
                user_id=user_id,
                phone=phone,
                country_code=country_code,
                session_file=session_file,
                price=price
            )
            session.add(record)
            session.commit()
            return record.id
        finally:
            session.close()
    
    def get_session_record(self, session_id: int):
        """获取 Session 记录"""
        session = self.get_session()
        try:
            return session.query(Session).filter_by(id=session_id).first()
        finally:
            session.close()
    
    def approve_session(self, session_id: int, reviewer_id: int):
        """通过 Session 审核"""
        session = self.get_session()
        try:
            record = session.query(Session).filter_by(id=session_id).first()
            if record:
                record.status = SessionStatus.APPROVED
                record.reviewed_at = datetime.utcnow()
                record.reviewer_id = reviewer_id
                
                # 增加用户余额
                user = session.query(User).filter_by(user_id=record.user_id).first()
                if user:
                    user.balance += record.price
                
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def reject_session(self, session_id: int, reviewer_id: int, reason: str):
        """拒绝 Session 审核"""
        session = self.get_session()
        try:
            record = session.query(Session).filter_by(id=session_id).first()
            if record:
                record.status = SessionStatus.REJECTED
                record.reviewed_at = datetime.utcnow()
                record.reviewer_id = reviewer_id
                record.reject_reason = reason
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_price(self, country_code: str, default_price: float = 0.2):
        """获取价格"""
        session = self.get_session()
        try:
            price_record = session.query(Price).filter_by(country_code=country_code).first()
            if price_record:
                return price_record.price, price_record.country_name, price_record.flag_emoji
            return default_price, None, None
        finally:
            session.close()
    
    def set_price(self, country_code: str, country_name: str, flag_emoji: str, price: float):
        """设置价格"""
        session = self.get_session()
        try:
            price_record = session.query(Price).filter_by(country_code=country_code).first()
            if price_record:
                price_record.price = price
                price_record.country_name = country_name
                price_record.flag_emoji = flag_emoji
                price_record.updated_at = datetime.utcnow()
            else:
                price_record = Price(
                    country_code=country_code,
                    country_name=country_name,
                    flag_emoji=flag_emoji,
                    price=price
                )
                session.add(price_record)
            session.commit()
            return True
        finally:
            session.close()
    
    def get_all_prices(self):
        """获取所有价格"""
        session = self.get_session()
        try:
            return session.query(Price).all()
        finally:
            session.close()
    
    def create_withdrawal(self, user_id: int, amount: float, fee: float, trc20_address: str):
        """创建提现申请"""
        session = self.get_session()
        try:
            withdrawal = Withdrawal(
                user_id=user_id,
                amount=amount,
                fee=fee,
                trc20_address=trc20_address
            )
            session.add(withdrawal)
            
            # 扣除余额
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.balance -= (amount + fee)
            
            session.commit()
            return withdrawal.id
        finally:
            session.close()
    
    def complete_withdrawal(self, withdrawal_id: int, admin_id: int):
        """完成提现"""
        session = self.get_session()
        try:
            withdrawal = session.query(Withdrawal).filter_by(id=withdrawal_id).first()
            if withdrawal:
                withdrawal.status = WithdrawalStatus.COMPLETED
                withdrawal.completed_at = datetime.utcnow()
                withdrawal.admin_id = admin_id
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_withdrawal(self, withdrawal_id: int):
        """获取提现记录"""
        session = self.get_session()
        try:
            return session.query(Withdrawal).filter_by(id=withdrawal_id).first()
        finally:
            session.close()
