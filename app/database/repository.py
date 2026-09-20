"""Združljivost: kanonični modul je `customer_repository`."""

from app.database.customer_repository import CustomerRepository, customer_repository

__all__ = ["CustomerRepository", "customer_repository"]
