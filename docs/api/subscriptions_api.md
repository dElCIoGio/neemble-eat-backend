# Plans, Subscriptions and Payments API

This document summarizes the endpoints related to subscription plans, user subscriptions and payments.

## Plans
- **GET /api/v1/plans/paginate** – Paginate subscription plans.
- **POST /api/v1/plans/** – Create a new plan.
- **PUT /api/v1/plans/plan/{plan_id}** – Update an existing plan.
- **DELETE /api/v1/plans/plan/{plan_id}** – Remove a plan.
- **GET /api/v1/plans/plan/{plan_id}** – Retrieve one plan.
- **GET /api/v1/plans/** – List active plans only.
- **GET /api/v1/plans/all** – List every plan regardless of status.

## Subscriptions
- **GET /api/v1/subscriptions/paginate** – Paginate user subscriptions.
- **POST /api/v1/subscriptions/subscribe** – Subscribe a user to a plan.
- **POST /api/v1/subscriptions/unsubscribe/{subscription_id}** – Cancel a subscription.
- **POST /api/v1/subscriptions/change-plan** – Switch the current plan.
- **GET /api/v1/subscriptions/users/{user_id}/current** – Get the current plan for a user.
- **GET /api/v1/subscriptions/current** – Return the authenticated user's subscription info.
- **GET /api/v1/subscriptions/usage** – Usage metrics for the authenticated user.
- **POST /api/v1/subscriptions/{subscription_id}/pause** – Temporarily pause a subscription.
- **POST /api/v1/subscriptions/{subscription_id}/resume** – Resume a paused subscription.
- **GET /api/v1/subscriptions/backup** – Download a backup of account data.

## Payments
- **GET /api/v1/payments/history** – List payment records for the active subscription.
- **POST /api/v1/payments/proofs** – Upload a payment proof file.
- **GET /api/v1/payments/latest-invoice** – Download the latest invoice.
- **GET /api/v1/payments/invoice/{payment_id}** – Download an invoice by payment id.
