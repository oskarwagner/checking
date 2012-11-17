"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import schema
from sqlalchemy.ext.declarative import declarative_base

__all__ = ["Session", "metadata", "BaseObject" ]

# SQLAlchemy session manager.  Updated by model.setupEngine()
Session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
metadata = schema.MetaData()

# Base classes for models using declarative syntax
BaseObject = declarative_base(metadata=metadata)

