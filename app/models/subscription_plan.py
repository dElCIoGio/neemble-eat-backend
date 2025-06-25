from app.db.crud import MongoCrud
from app.schema import subscription_plan as plan_schema

class SubscriptionPlanModel(MongoCrud[plan_schema.SubscriptionPlanDocument]):
    def __init__(self) -> None:
        super().__init__(plan_schema.SubscriptionPlanDocument)
