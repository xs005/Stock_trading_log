import fileinput
import json
from collections import defaultdict

# It requires to build a class in the OA.
class Company:
    def __init__(self, name):
        self.name = name
        self.own = 0
        self.sell = 0
        self.buy = 0

class MarkingPositionMonitor:
    def __init__(self):
        self.company_dict = {}
        self.order_dict = {}

    def on_event(self, message):
        m_dict = json.loads(message)

        if m_dict["type"] == "NEW":
            order_id = m_dict["order_id"]
            self.order_dict[order_id] = m_dict
            company_name = m_dict["symbol"]
            # create company instance in dict if not exist.
            if company_name not in self.company_dict:
                self.company_dict[company_name] = Company(company_name)
            # immediately change the quantity.
            if m_dict["side"] == "SELL":
                self.company_dict[company_name].sell += int(m_dict["quantity"])
            # new order to buy does not affect marking postion.
            if m_dict["side"] == "BUY":
                self.company_dict[company_name].buy += int(m_dict["quantity"])
            return self.company_dict[company_name].own - self.company_dict[company_name].sell

        if m_dict["type"] == "ORDER_REJECT" or m_dict["type"] == "CANCEL_ACK":
            # read the history order message detail from order_id
            order_id = m_dict["order_id"]
            order_detail = self.order_dict[order_id]
            company_name = order_detail["symbol"]
            # immediately change sell quantity
            if order_detail["side"] == "SELL":
                self.company_dict[company_name].sell -= int(order_detail["quantity"])
            if order_detail["side"] == "BUY":
                self.company_dict[company_name].buy -= int(order_detail["quantity"])
            return self.company_dict[company_name].own - self.company_dict[company_name].sell

        if m_dict["type"] == "CANCEL" or m_dict["type"] == "CANCEL_REJECT" or m_dict["type"] == "ORDER_ACK":
            # try to cancel stated; no immediate effect.
            order_id = m_dict["order_id"]
            order_detail = self.order_dict[order_id]
            company_name = order_detail["symbol"]
            return self.company_dict[company_name].own - self.company_dict[company_name].sell

        if m_dict["type"] == "FILL":
            order_id = m_dict["order_id"]
            order_detail = self.order_dict[order_id]
            company_name = order_detail["symbol"]
            if "filled_quantity" not in order_detail:
                order_detail["filled_quantity"] = 0
            if order_detail["side"] == "SELL":
                order_detail["filled_quantity"] = m_dict["filled_quantity"]
            if order_detail["side"] == "BUY":
                self.company_dict[company_name].own -= order_detail["filled_quantity"] #  minus bought quantity from this order
                order_detail["filled_quantity"] = m_dict["filled_quantity"]
                self.company_dict[company_name].own += order_detail["filled_quantity"] # add current bought quantity from this order
            return self.company_dict[company_name].own - self.company_dict[company_name].sell

# Use the attached file to test this script.
if __name__ == '__main__':
    onn = MarkingPositionMonitor()
    for message in fileinput.input('input001.txt'):
        print(onn.on_event(message))


