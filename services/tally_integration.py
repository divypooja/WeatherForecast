import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TallyIntegration:
    """
    Tally ERP Integration Service
    Handles synchronization of accounting data between Factory Management System and Tally
    """
    
    def __init__(self, tally_host='localhost', tally_port=9000):
        self.tally_host = tally_host
        self.tally_port = tally_port
        self.base_url = f"http://{tally_host}:{tally_port}"
        
    def test_connection(self) -> Dict:
        """Test connection to Tally"""
        try:
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Import Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <IMPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>List of Companies</REPORTNAME>
                        </REQUESTDESC>
                    </IMPORTDATA>
                </BODY>
            </ENVELOPE>
            """
            response = requests.post(self.base_url, data=xml_request, timeout=10)
            if response.status_code == 200:
                return {"status": "success", "message": "Connected to Tally successfully"}
            else:
                return {"status": "error", "message": f"Connection failed: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {str(e)}"}
    
    def sync_suppliers(self, suppliers: List) -> Dict:
        """Sync suppliers/vendors to Tally as Ledgers"""
        try:
            xml_data = self._build_ledger_xml(suppliers)
            response = requests.post(self.base_url, data=xml_data)
            
            if response.status_code == 200:
                return {"status": "success", "synced": len(suppliers), "message": "Suppliers synced successfully"}
            else:
                return {"status": "error", "message": f"Sync failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"Supplier sync error: {str(e)}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
    
    def sync_items(self, items: List) -> Dict:
        """Sync inventory items to Tally as Stock Items"""
        try:
            xml_data = self._build_stock_items_xml(items)
            response = requests.post(self.base_url, data=xml_data)
            
            if response.status_code == 200:
                return {"status": "success", "synced": len(items), "message": "Items synced successfully"}
            else:
                return {"status": "error", "message": f"Sync failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"Items sync error: {str(e)}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
    
    def sync_purchase_orders(self, purchase_orders: List) -> Dict:
        """Sync purchase orders to Tally as Purchase Vouchers"""
        try:
            synced_count = 0
            errors = []
            
            for po in purchase_orders:
                xml_data = self._build_purchase_voucher_xml(po)
                response = requests.post(self.base_url, data=xml_data)
                
                if response.status_code == 200:
                    synced_count += 1
                else:
                    errors.append(f"PO {po.po_number}: {response.status_code}")
            
            if errors:
                return {"status": "partial", "synced": synced_count, "errors": errors}
            else:
                return {"status": "success", "synced": synced_count, "message": "Purchase Orders synced successfully"}
                
        except Exception as e:
            logger.error(f"Purchase orders sync error: {str(e)}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
    
    def sync_sales_orders(self, sales_orders: List) -> Dict:
        """Sync sales orders to Tally as Sales Vouchers"""
        try:
            synced_count = 0
            errors = []
            
            for so in sales_orders:
                xml_data = self._build_sales_voucher_xml(so)
                response = requests.post(self.base_url, data=xml_data)
                
                if response.status_code == 200:
                    synced_count += 1
                else:
                    errors.append(f"SO {so.so_number}: {response.status_code}")
            
            if errors:
                return {"status": "partial", "synced": synced_count, "errors": errors}
            else:
                return {"status": "success", "synced": synced_count, "message": "Sales Orders synced successfully"}
                
        except Exception as e:
            logger.error(f"Sales orders sync error: {str(e)}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
    
    def sync_expenses(self, expenses: List) -> Dict:
        """Sync factory expenses to Tally as Journal Vouchers"""
        try:
            synced_count = 0
            errors = []
            
            for expense in expenses:
                xml_data = self._build_expense_voucher_xml(expense)
                response = requests.post(self.base_url, data=xml_data)
                
                if response.status_code == 200:
                    synced_count += 1
                else:
                    errors.append(f"Expense {expense.expense_number}: {response.status_code}")
            
            if errors:
                return {"status": "partial", "synced": synced_count, "errors": errors}
            else:
                return {"status": "success", "synced": synced_count, "message": "Expenses synced successfully"}
                
        except Exception as e:
            logger.error(f"Expenses sync error: {str(e)}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
    
    def _build_ledger_xml(self, suppliers: List) -> str:
        """Build XML for supplier ledgers"""
        xml_parts = [
            '<ENVELOPE>',
            '<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
            '<BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>',
            '<REQUESTDATA>'
        ]
        
        for supplier in suppliers:
            ledger_xml = f"""
            <TALLYMESSAGE xmlns:UDF="TallyUDF">
                <LEDGER NAME="{supplier.name}" RESERVEDNAME="">
                    <GUID>{supplier.id}</GUID>
                    <PARENT>Sundry Creditors</PARENT>
                    <GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>
                    <GSTIN>{supplier.gst_number or ''}</GSTIN>
                    <PARTYGSTIN>{supplier.gst_number or ''}</PARTYGSTIN>
                    <ADDRESS.LIST>
                        <ADDRESS>{supplier.address or ''}</ADDRESS>
                        <ADDRESS>{supplier.city or ''}, {supplier.state or ''} - {supplier.pin_code or ''}</ADDRESS>
                    </ADDRESS.LIST>
                    <EMAIL>{supplier.email or ''}</EMAIL>
                    <PHONE>{supplier.phone or ''}</PHONE>
                    <CONTACTPERSON>{supplier.contact_person or ''}</CONTACTPERSON>
                    <BANKINGCONFIG.LIST>
                        <ACCOUNTNUMBER>{supplier.account_number or ''}</ACCOUNTNUMBER>
                        <BANKNAME>{supplier.bank_name or ''}</BANKNAME>
                        <IFSCODE>{supplier.ifsc_code or ''}</IFSCODE>
                    </BANKINGCONFIG.LIST>
                </LEDGER>
            </TALLYMESSAGE>
            """
            xml_parts.append(ledger_xml)
        
        xml_parts.extend(['</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'])
        return ''.join(xml_parts)
    
    def _build_stock_items_xml(self, items: List) -> str:
        """Build XML for stock items"""
        xml_parts = [
            '<ENVELOPE>',
            '<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
            '<BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>',
            '<REQUESTDATA>'
        ]
        
        for item in items:
            stock_item_xml = f"""
            <TALLYMESSAGE xmlns:UDF="TallyUDF">
                <STOCKITEM NAME="{item.name}" RESERVEDNAME="">
                    <GUID>{item.id}</GUID>
                    <PARENT/>
                    <BASEUNITS>{item.unit_of_measure}</BASEUNITS>
                    <GSTAPPLICABLE>Applicable</GSTAPPLICABLE>
                    <GSTTYPEOFSUPPLY>Goods</GSTTYPEOFSUPPLY>
                    <GSTRATE>{item.gst_rate}</GSTRATE>
                    <HSNCODE>{item.hsn_code or ''}</HSNCODE>
                    <DESCRIPTION>{item.description or ''}</DESCRIPTION>
                    <COSTINGMETHOD>FIFO</COSTINGMETHOD>
                    <VALUATIONMETHOD>Avg. Cost</VALUATIONMETHOD>
                    <OPENINGBALANCE>{item.current_stock}</OPENINGBALANCE>
                    <OPENINGRATE>{item.unit_price}</OPENINGRATE>
                    <OPENINGVALUE>{item.current_stock * item.unit_price}</OPENINGVALUE>
                </STOCKITEM>
            </TALLYMESSAGE>
            """
            xml_parts.append(stock_item_xml)
        
        xml_parts.extend(['</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'])
        return ''.join(xml_parts)
    
    def _build_purchase_voucher_xml(self, po) -> str:
        """Build XML for purchase voucher"""
        voucher_xml = f"""
        <ENVELOPE>
            <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
            <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Purchase" ACTION="Create">
                        <GUID>{po.id}</GUID>
                        <DATE>{po.order_date.strftime('%Y%m%d')}</DATE>
                        <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{po.po_number}</VOUCHERNUMBER>
                        <PARTYLEDGERNAME>{po.supplier.name}</PARTYLEDGERNAME>
                        <BASICBUYERADDRESS.LIST>
                            <BASICBUYERADDRESS>{po.supplier.address or ''}</BASICBUYERADDRESS>
                        </BASICBUYERADDRESS.LIST>
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{po.supplier.name}</LEDGERNAME>
                            <GSTCLASS/>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{po.total_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
        """
        
        for item in po.items:
            voucher_xml += f"""
                        <ALLINVENTORYENTRIES.LIST>
                            <STOCKITEMNAME>{item.item.name}</STOCKITEMNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <RATE>{item.rate}</RATE>
                            <AMOUNT>{item.amount}</AMOUNT>
                            <ACTUALQTY>{item.quantity} {item.item.unit_of_measure}</ACTUALQTY>
                            <BILLEDQTY>{item.quantity} {item.item.unit_of_measure}</BILLEDQTY>
                        </ALLINVENTORYENTRIES.LIST>
            """
        
        voucher_xml += """
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA></IMPORTDATA></BODY>
        </ENVELOPE>
        """
        return voucher_xml
    
    def _build_sales_voucher_xml(self, so) -> str:
        """Build XML for sales voucher"""
        voucher_xml = f"""
        <ENVELOPE>
            <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
            <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Sales" ACTION="Create">
                        <GUID>{so.id}</GUID>
                        <DATE>{so.order_date.strftime('%Y%m%d')}</DATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{so.so_number}</VOUCHERNUMBER>
                        <PARTYLEDGERNAME>{so.customer.name}</PARTYLEDGERNAME>
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{so.customer.name}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{so.total_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
        """
        
        for item in so.items:
            voucher_xml += f"""
                        <ALLINVENTORYENTRIES.LIST>
                            <STOCKITEMNAME>{item.item.name}</STOCKITEMNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <RATE>{item.rate}</RATE>
                            <AMOUNT>-{item.amount}</AMOUNT>
                            <ACTUALQTY>-{item.quantity} {item.item.unit_of_measure}</ACTUALQTY>
                            <BILLEDQTY>-{item.quantity} {item.item.unit_of_measure}</BILLEDQTY>
                        </ALLINVENTORYENTRIES.LIST>
            """
        
        voucher_xml += """
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA></IMPORTDATA></BODY>
        </ENVELOPE>
        """
        return voucher_xml
    
    def _build_expense_voucher_xml(self, expense) -> str:
        """Build XML for expense journal voucher"""
        voucher_xml = f"""
        <ENVELOPE>
            <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
            <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Journal" ACTION="Create">
                        <GUID>{expense.id}</GUID>
                        <DATE>{expense.expense_date.strftime('%Y%m%d')}</DATE>
                        <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{expense.expense_number}</VOUCHERNUMBER>
                        <NARRATION>{expense.description}</NARRATION>
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{expense.category} Expenses</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{expense.amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>Cash</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{expense.amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA></IMPORTDATA></BODY>
        </ENVELOPE>
        """
        return voucher_xml

# Initialize Tally service
tally_service = TallyIntegration()