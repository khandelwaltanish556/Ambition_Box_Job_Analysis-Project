from flask import Flask, render_template, request, flash # type: ignore
import plotly.express as px # type: ignore
import pandas as pd # pyright: ignore[reportMissingModuleSource]
import dataset   # ✅ data loader file ka naya naam

app = Flask(__name__)
app.secret_key = "change-this"

# Load dataset at startup
df = dataset.load_data("csv_files")

def has_col(col):
    return col in df.columns

@app.route("/")
def home():
    return render_template(
        "index.html",
        locations=sorted(df["location"].dropna().unique()) if has_col("location") else [],
        industries=sorted(df["industry"].dropna().unique()) if has_col("industry") else [],
        ratings=sorted(pd.to_numeric(df["company_rating"], errors="coerce").dropna().unique()) if has_col("company_rating") else [],
        types=sorted(df["type"].dropna().unique()) if has_col("type") else []
    )

@app.route("/submit", methods=["POST"])
def submit():
    # --- Collect filters ---
    location = request.form.get("location") or ""
    industry = request.form.get("industry") or ""
    rating = request.form.get("rating") or ""
    comp_type = request.form.get("type") or ""
    output = request.form.get("output") or "table"

    # --- Apply filters ---
    filtered = df.copy()
    if location and has_col("location"):
        filtered = filtered[filtered["location"] == location]
    if industry and has_col("industry"):
        filtered = filtered[filtered["industry"] == industry]
    if rating and has_col("company_rating"):
        filtered = filtered[pd.to_numeric(filtered["company_rating"], errors="coerce") >= float(rating)]
    if comp_type and has_col("type"):
        filtered = filtered[filtered["type"] == comp_type]

    # --- If no data ---
    if filtered.empty:
        flash("⚠️ No records matched your filters.")
        return render_template("table.html", table="<p class='text-center m-0'>No data</p>", titles=[])

    # --- If table requested ---
    if output == "table":
        table_html = filtered.to_html(
            classes="table table-striped table-bordered table-hover text-center align-middle",
            index=False, border=0, justify="center"
        )
        return render_template("table.html", table=table_html, titles=list(filtered.columns))

    # --- Chart output ---
    px.defaults.template = "plotly_white"
    px.defaults.width = 850
    px.defaults.height = 450

    # Clean numeric values
    for col in ["company_rating", "years_old", "size"]:
        if col in filtered.columns:
            filtered[col] = pd.to_numeric(filtered[col], errors="coerce").fillna(0)

    # Chart 1: Rating vs Company
    if {"company_rating", "company_name"}.issubset(filtered.columns):
        fig1 = px.scatter(
            filtered, x="company_rating", y="company_name",
            color="industry" if has_col("industry") else None,
            size="years_old" if has_col("years_old") else None,
            title="Rating vs Company Name"
        )
    else:
        fig1 = px.scatter(title="Data missing")

    # Chart 2: Ratings Distribution
    if {"company_name", "company_rating"}.issubset(filtered.columns):
        fig2 = px.bar(
            filtered.sort_values("company_rating", ascending=False),
            x="company_name", y="company_rating",
            color="industry" if has_col("industry") else None,
            title="Company Ratings Distribution"
        )
        fig2.update_layout(xaxis_tickangle=45)
    else:
        fig2 = px.bar(title="Data missing")

    # Chart 3: Company Age
    if {"company_name", "years_old"}.issubset(filtered.columns):
        fig3 = px.bar(
            filtered.sort_values("years_old", ascending=False),
            x="company_name", y="years_old",
            color="company_rating" if has_col("company_rating") else None,
            title="Company Age (Years)"
        )
        fig3.update_layout(xaxis_tickangle=45)
    else:
        fig3 = px.bar(title="Data missing")

    # Chart 4: Ratings by Industry
    if {"industry", "company_rating"}.issubset(filtered.columns):
        agg = filtered.groupby("industry")["company_rating"].mean().reset_index()
        fig4 = px.pie(
            agg, names="industry", values="company_rating",
            hole=0.4, title="Average Rating by Industry"
        )
    else:
        fig4 = px.pie(title="Data missing")

    # Chart 5: Age vs Rating (with safe size)
    if {"company_rating", "years_old"}.issubset(filtered.columns):
        size_col = "size" if has_col("size") else None
        fig5 = px.scatter(
            filtered, x="company_rating", y="years_old",
            color="industry" if has_col("industry") else None,
            size=size_col,
            hover_name="company_name" if has_col("company_name") else None,
            title="Age vs Rating"
        )
    else:
        fig5 = px.scatter(title="Data missing")

    # Chart 6: Rating by Size
    if {"size", "company_rating"}.issubset(filtered.columns):
        fig6 = px.bar(
            filtered.sort_values("size", ascending=False),
            x="size", y="company_rating",
            color="industry" if has_col("industry") else None,
            title="Rating by Company Size"
        )
    else:
        fig6 = px.bar(title="Data missing")

    # --- Return charts ---
    return render_template(
        "charts.html",
        chart1=fig1.to_html(full_html=False, include_plotlyjs="cdn"),
        chart2=fig2.to_html(full_html=False, include_plotlyjs=False),
        chart3=fig3.to_html(full_html=False, include_plotlyjs=False),
        chart4=fig4.to_html(full_html=False, include_plotlyjs=False),
        chart5=fig5.to_html(full_html=False, include_plotlyjs=False),
        chart6=fig6.to_html(full_html=False, include_plotlyjs=False)
    )

@app.route("/health")
def health():
    return {"status": "ok", "rows": int(len(df))}

if __name__ == "__main__":
    app.run(debug=True, port=5002)
