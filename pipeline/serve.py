import os
import matplotlib.pyplot as plt

def run(top_products, top_customers, output_folder):

    # Save analytics to CSV
    top_products.to_csv(
        f"{output_folder}/top_products.csv",
        index=False
    )

    top_customers.to_csv(
        f"{output_folder}/top_customers.csv",
        index=False
    )

    print(
        f"Saved analytics to: "
        f"{output_folder}/top_products.csv "
        f"and top_customers.csv"  
    )

# -------------------------------
# Top Products Chart
# -------------------------------

plt.figure(figsize=(8, 4))

plt.bar(
    top_products["product_name"],
    top_products["total_revenue"],
    color="skyblue"
)

plt.title("Top 3 Products by Revenue")
plt.ylabel("Revenue")
plt.tight_layout()

products_chart_path = os.path.join(
    output_folder,
    "top_products.png"
)

plt.savefig(products_chart_path)

plt.close()

print(
    f"Chart saved to: "
    f"{products_chart_path}"
)

# -------------------------------
# Top Customers Chart
# -------------------------------

plt.figure(figsize=(8, 4))

plt.bar(
    top_customers["customer_name"],
    top_customers["total_spend"],
    color="orange"
)

plt.title("Top 3 Customers by Spend")
plt.ylabel("Total Spend")
plt.tight_layout()

customers_chart_path = os.path.join(
    output_folder,
    "top_customers.png"
)

plt.savefig(customers_chart_path)

plt.close()

print(
    f"Chart saved to: "
    f"{customers_chart_path}"
)