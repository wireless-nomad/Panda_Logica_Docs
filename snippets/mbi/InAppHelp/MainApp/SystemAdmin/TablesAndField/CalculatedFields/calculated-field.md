# Define/Edit a Calculated Field

![Calculated Field Screen](Panda_Logica_Docs/snippets/mbi/InAppHelp/MainApp/images/calculated-field.png)

The **Define/Edit a Calculated Field** window allows MBI administrators
or advanced users to create custom computed fields that can be reused
across queries, dashboards, and pivot tables.

------------------------------------------------------------------------

## Overview

This screen is divided into **three main sections**:

1.  **Left Panel -- Table & Schema Selection**\
    Used to select the **Schema** and **Table** into which the new
    calculated field will be added.\
    Once selected, all field definitions are saved directly to that
    table's metadata, making the calculated field available globally in
    MBI.

2.  **Right Panel -- Field Description & Properties**\
    This panel defines the properties of the calculated field:

    -   **Field Name:** A unique name automatically prefixed with
        `*CALC`.\
    -   **Field Text:** A descriptive label for the field.\
    -   **Field Type:** Choose **Numeric** or **Alphanumeric**.\
    -   **Pivot Type:** Determines how the field behaves in pivot
        tables:
        -   **Measure** -- numeric value usable in aggregations
            (e.g. sums, averages)\
        -   **Data Item** -- treated as a dimension or category\
        -   **None** -- excluded from pivot usage entirely\
    -   **Decimal Places:** Defines numeric precision when applicable.

3.  **Field Expression -- Formula Definition**\
    Located below the property panels, this section allows you to define
    the actual formula or logic behind the calculated field.\
    This can include:

    -   Simple arithmetic, e.g. `Quantity * Price`
    -   String operations or concatenation
    -   SQL `SELECT` expressions for aggregated or cross-table summaries

Examples:

``` sql
-- Basic numeric calculation
[QTY] * [PRICE]

-- String concatenation
CONCAT([FIRST_NAME], ' ', [LAST_NAME])

-- SQL-based summary
SELECT SUM(SALESAMT) FROM SOITEM WHERE YEAR(ORDERDATE) = 2024
```

------------------------------------------------------------------------

## Adding the Field

Once all settings are defined, click **Add New Calculated Field** at the
top of the form.\
This will permanently add the field definition to the selected table,
making it visible in all query builders and dashboards that reference
that table.

------------------------------------------------------------------------

## Notes & Best Practices

-   Maintain consistent naming conventions to make calculated fields
    easily recognisable.\
-   Keep expressions efficient; overly complex formulas may impact
    performance.\
-   Validate data types to prevent conversion issues during aggregation
    or display.\
-   Calculated fields are stored at table level --- editing or deleting
    them affects all dependent queries.

------------------------------------------------------------------------

*End of document.*
