from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)


metadata = MetaData()


# --------------------------------------------------
# Pipeline batch control table
# --------------------------------------------------

pipeline_batches = Table(
    "pipeline_batches",
    metadata,

    Column(
        "batch_id",
        String(255),
        primary_key=True
    ),

    Column(
        "status",
        String(20),
        nullable=False
    ),

    Column(
        "rows_loaded",
        Integer,
        nullable=False,
        default=0
    ),

    Column(
        "started_at",
        DateTime(timezone=True),
        nullable=False
    ),

    Column(
        "completed_at",
        DateTime(timezone=True),
        nullable=True
    ),

    CheckConstraint(
        "status IN ('RUNNING', 'SUCCESS', 'FAILED')",
        name="ck_pipeline_batches_status"
    )
)


# --------------------------------------------------
# Enriched orders
# --------------------------------------------------

orders_enriched = Table(
    "orders_enriched",
    metadata,

    Column(
        "order_id",
        Integer,
        nullable=False,
        primary_key=True
    ),

    Column(
        "customer_id",
        Integer,
        nullable=False
    ),

    Column(
        "product_id",
        Integer,
        nullable=False
    ),

    Column(
        "quantity",
        Integer,
        nullable=False
    ),

    Column(
        "order_date",
        Date,
        nullable=False
    ),

    Column(
        "product_name",
        String(255),
        nullable=False
    ),

    Column(
        "price",
        Float,
        nullable=False
    ),

    Column(
        "customer_name",
        String(255),
        nullable=False
    ),

    Column(
        "line_total",
        Float,
        nullable=False
    ),

    Column(
        "batch_id",
        String(255),
        ForeignKey("pipeline_batches.batch_id"),
        nullable=False,
        primary_key=True
    ),

    Column(
        "loaded_at",
        DateTime(timezone=True),
        nullable=False
    )
)


# --------------------------------------------------
# Product analytics
# --------------------------------------------------

top_products = Table(
    "top_products",
    metadata,

    Column(
        "product_id",
        Integer,
        nullable=False,
        primary_key=True
    ),

    Column(
        "product_name",
        String(255),
        nullable=False
    ),

    Column(
        "total_revenue",
        Float,
        nullable=False
    ),

    Column(
        "batch_id",
        String(255),
        ForeignKey("pipeline_batches.batch_id"),
        nullable=False,
        primary_key=True
    ),

    Column(
        "loaded_at",
        DateTime(timezone=True),
        nullable=False
    )
)


# --------------------------------------------------
# Customer analytics
# --------------------------------------------------

top_customers = Table(
    "top_customers",
    metadata,

    Column(
        "customer_id",
        Integer,
        nullable=False,
        primary_key=True
    ),

    Column(
        "customer_name",
        String(255),
        nullable=False
    ),

    Column(
        "total_spend",
        Float,
        nullable=False
    ),

    Column(
        "batch_id",
        String(255),
        ForeignKey("pipeline_batches.batch_id"),
        nullable=False,
        primary_key=True
    ),

    Column(
        "loaded_at",
        DateTime(timezone=True),
        nullable=False
    )
)


def create_tables(engine):
    """
    Create pipeline database tables that do not already exist.
    """

    metadata.create_all(engine)