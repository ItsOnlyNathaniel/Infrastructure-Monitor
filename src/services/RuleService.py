# Imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional, Dict, Any
import logging
from src.database.models import RemediationRules

logger = logging.getLogger(__name__)


class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Get a single rule by ID"""
        rule_search = select(RemediationRules).where(RemediationRules.id == rule_id)
        result = await self.db.execute(rule_search)
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        return {
            "id": rule.id,
            "resource_type": rule.resource_type,
            "issue_type": rule.issue_type,
            "description": rule.description,
            "conditions": rule.conditions,
            "action": rule.action,
            "is_active": rule.is_active,
            "auto_execute": rule.auto_execute,
            "priority": rule.priority,
            "max_attempts": rule.max_attempts,
        }

    async def get_all_rules(
        self, resource_type: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get all rules, optionally filtered by resource_type and is_active"""
        rule_search = select(RemediationRules)

        if resource_type:
            rule_search = rule_search.where(RemediationRules.resource_type == resource_type)
        if is_active is not None:
            rule_search = rule_search.where(RemediationRules.is_active == is_active)

        rule_search = rule_search.order_by(RemediationRules.priority.desc(), RemediationRules.id)
        rule_result = await self.db.execute(rule_search)
        rules = rule_result.scalars().all()

        return [
            {
                "id": rule.id,
                "resource_type": rule.resource_type,
                "issue_type": rule.issue_type,
                "description": rule.description,
                "conditions": rule.conditions,
                "action": rule.action,
                "is_active": rule.is_active,
                "auto_execute": rule.auto_execute,
                "priority": rule.priority,
                "max_attempts": rule.max_attempts,
            }
            for rule in rules
        ]

    async def create_rule(
        self,
        resource_type: str,
        issue_type: str,
        action: str,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        auto_execute: bool = False,
        priority: int = 1,
        max_attempts: int = 3,
    ) -> int:
        """Create a new remediation rule"""
        rule = RemediationRules(
            resource_type=resource_type,
            issue_type=issue_type,
            description=description,
            conditions=conditions or {},
            action=action,
            is_active=is_active,
            auto_execute=auto_execute,
            priority=priority,
            max_attempts=max_attempts,
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info("Created rule %s for %s: %s", rule.id, resource_type, issue_type)
        return rule.id

    async def update_rule(
        self,
        rule_id: int,
        resource_type: Optional[str] = None,
        issue_type: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        action: Optional[str] = None,
        is_active: Optional[bool] = None,
        auto_execute: Optional[bool] = None,
        priority: Optional[int] = None,
        max_attempts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update an existing rule"""
        rule_search = select(RemediationRules).where(RemediationRules.id == rule_id)
        rule_result = await self.db.execute(rule_search)
        rule = rule_result.scalar_one_or_none()

        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        # Update only provided fields
        if resource_type is not None:
            rule.resource_type = resource_type
        if issue_type is not None:
            rule.issue_type = issue_type
        if description is not None:
            rule.description = description
        if conditions is not None:
            rule.conditions = conditions
        if action is not None:
            rule.action = action
        if is_active is not None:
            rule.is_active = is_active
        if auto_execute is not None:
            rule.auto_execute = auto_execute
        if priority is not None:
            rule.priority = priority
        if max_attempts is not None:
            rule.max_attempts = max_attempts

        await self.db.commit()
        await self.db.refresh(rule)

        logger.info("Updated rule %s", rule_id)

        return {
            "id": rule.id,
            "resource_type": rule.resource_type,
            "issue_type": rule.issue_type,
            "description": rule.description,
            "conditions": rule.conditions,
            "action": rule.action,
            "is_active": rule.is_active,
            "auto_execute": rule.auto_execute,
            "priority": rule.priority,
            "max_attempts": rule.max_attempts,
        }

    async def delete_rule(self, rule_id: int) -> None:
        """Delete a rule by ID"""
        rule_search = select(RemediationRules).where(RemediationRules.id == rule_id)
        rule_result = await self.db.execute(rule_search)
        rule = rule_result.scalar_one_or_none()

        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        delete_stmt = delete(RemediationRules).where(RemediationRules.id == rule_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()

        logger.info("Deleted rule %s", rule_id)

    async def toggle_rule_status(self, rule_id: int, is_active: bool) -> Dict[str, Any]:
        """Toggle the active status of a rule"""
        return await self.update_rule(rule_id, is_active=is_active)
