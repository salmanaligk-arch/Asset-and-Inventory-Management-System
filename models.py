from dataclasses import dataclass
from typing import Optional

@dataclass
class Category:
    category_id: Optional[int] = None
    category_name: str = ""
    remarks: str = ""

@dataclass
class SubCategory:
    subcategory_id: Optional[int] = None
    category_id: int = 0
    subcategory_name: str = ""
    remarks: str = ""

@dataclass
class Branch:
    branch_id: Optional[int] = None
    branch_name: str = ""
    address: str = ""
    remarks: str = ""

@dataclass
class Item:
    item_id: Optional[int] = None
    item_name: str = ""
    category_id: int = 0
    subcategory_id: int = 0
    specification: str = ""
    govt_property_code: str = ""
    remarks: str = ""

@dataclass
class AssetBatch:
    batch_id: Optional[int] = None
    item_id: int = 0
    branch_id: int = 0
    acquisition_date: str = ""
    acquisition_method: str = ""
    source: str = ""
    quantity: int = 0
    cost: float = 0.0
    authority_ref: str = ""
    remarks: str = ""
    acquisition_year: str = ""

@dataclass
class AssetTransaction:
    transaction_id: Optional[int] = None
    batch_id: int = 0
    transaction_type: str = ""
    from_branch_id: Optional[int] = None
    to_branch_id: Optional[int] = None
    transaction_date: str = ""
    quantity: int = 0
    authority_ref: str = ""
    remarks: str = ""

@dataclass
class AssetDisposal:
    disposal_id: Optional[int] = None
    batch_id: int = 0
    disposal_date: str = ""
    quantity: int = 0
    disposal_method: str = ""
    authority_ref: str = ""
    remarks: str = ""

@dataclass
class User:
    user_id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = ""