"""
Stock Extractor Module
Specialized module for extracting stock/inventory data from stkm_main_all
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from .database_extractor import DatabaseExtractor
from scm_training.config import MAPPING_FILE

logger = logging.getLogger(__name__)


class StockExtractor:
    """Class for extracting stock/inventory data with company-based data isolation"""

    def __init__(self, config_path: str = None, companyfn: Optional[str] = None, masterfn: Optional[str] = None):
        """
        Initialize StockExtractor

        Args:
            config_path: Path to configuration file
            companyfn: Company code for data isolation (unique per company)
        """
        self.db_extractor = DatabaseExtractor(config_path)
        self.mapping = self._load_mapping()
        self.companyfn = companyfn
        self.masterfn = masterfn

    def _load_mapping(self) -> Dict:
        """Read mapping file"""
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Mapping file mapping.json not found")
            return {}

    def _effective_companyfn(self, companyfn: Optional[str] = None) -> Optional[str]:
        return companyfn or self.companyfn

    def _effective_masterfn(self, masterfn: Optional[str] = None) -> Optional[str]:
        return masterfn or self.masterfn

    def extract_stock_main(
        self,
        companyfn: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        transaction_types: Optional[List[str]] = None,
        include_void: bool = False
    ) -> pd.DataFrame:
        """
        Extract data from stkm_main_all table with company-based data isolation

        Args:
            companyfn: Company code (uses instance companyfn if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            transaction_types: Transaction types (stk_doc, stk_do, stk_gvn, etc.)
            include_void: Include voided transactions

        Returns:
            DataFrame containing data filtered by companyfn
        """
        try:
            # Use instance companyfn if not provided (for data isolation)
            effective_companyfn = self._effective_companyfn(companyfn)
            effective_masterfn = self._effective_masterfn()

            # Build filters
            filters = {}

            if effective_companyfn:
                filters['companyfn'] = effective_companyfn

            if not include_void:
                filters['tag_void_yn'] = 'n'

            if transaction_types:
                filters['tag_table_usage'] = transaction_types

            query = """
                SELECT
                    uniquenum_pri,
                    companyfn,
                    tag_table_usage,
                    date_trans,
                    location_code,
                    stkcode_code,
                    stkcode_unique,
                    balance_qnty_uom_stk_code,
                    party_unique,
                    party_code,
                    party_desc,
                    staff_code,
                    staff_unique,
                    tag_void_yn,
                    amount_local,
                    amount_forex,
                    curr_short_forex
                FROM stkm_main_all
                WHERE 1=1
            """

            params = {}

            if effective_companyfn:
                query += " AND companyfn = :companyfn"
                params['companyfn'] = effective_companyfn

            if effective_masterfn:
                query += " AND masterfn = :masterfn"
                params['masterfn'] = effective_masterfn

            if date_from:
                query += " AND date_trans >= :date_from"
                params['date_from'] = date_from

            if date_to:
                query += " AND date_trans <= :date_to"
                params['date_to'] = date_to

            query += " ORDER BY date_trans DESC"

            logger.info(f"Extracting stkm_main_all | params: {params}")
            result = self.db_extractor.extract_data(query, params)
            logger.info(f"Result: {len(result)} records")
            return result

        except Exception as e:
            logger.error(f"Error extracting stkm_main_all: {str(e)}")
            raise

    def close(self):
        """Close connection"""
        self.db_extractor.close()
