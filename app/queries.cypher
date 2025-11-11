// Clear everything (careful in real life!)
MATCH (n) DETACH DELETE n;

// Constraints to avoid duplicates
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
FOR (c:Customer) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT category_id_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT order_id_unique IF NOT EXISTS
FOR (o:Order) REQUIRE o.id IS UNIQUE;

// Optional: simple indexes for names
CREATE INDEX category_name_index IF NOT EXISTS
FOR (c:Category) ON (c.name);

CREATE INDEX product_name_index IF NOT EXISTS
FOR (p:Product) ON (p.name);
