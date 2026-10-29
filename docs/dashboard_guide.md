# Building the Kroma dashboard in Tableau Public

No installation needed: Tableau Public works in the browser. Data comes from `exports/kroma_dashboard_data.xlsx`
(created by `python python/export_for_tableau.py`).

## 1. Get the data file
In the Codespace Explorer, right-click `exports/kroma_dashboard_data.xlsx` → **Download**.

## 2. Open Tableau Public
Go to **public.tableau.com**, sign in (free account), then **Create → Web Authoring**.
Under **Connect to Data**, choose **Upload from computer** and select the Excel file.
Drag the **funnel_weekly** sheet onto the canvas. For each later view, add another data source:
**Data → New Data Source → Upload** the same file, and drag the sheet you need.

## 3. Build five views (one Tableau "sheet" each)

**View 1 · Conversion by device** (data: funnel_weekly)
1. Create a calculated field `Conversion` = `SUM([Purchased]) / SUM([Sessions])`. Format as percentage.
2. Drag **Device** to Rows and **Conversion** to Columns. Sort descending. Show labels.
3. Title: *Mobile converts at 3.4% vs 5.3% on desktop*.

**View 2 · Weekly conversion trend** (data: funnel_weekly)
1. Drag **Session Week** to Columns (right-click → *Week*, continuous), **Conversion** to Rows, **Device** to Color.
2. Title: *Weekly conversion by device*.

**View 3 · Experiment lift by device** (data: experiment)
1. Drag **Segment** to Rows and **Diff Pp** to Columns (bar chart). Show labels.
2. Add a reference line at 1.0 on the Diff Pp axis, labelled *MDE (+1.0 pp)*.
3. Title: *Simplified checkout: +0.66 pp overall, driven by mobile*.

**View 4 · Acquisition quality** (data: acquisition)
1. Create `Buyer rate 30d` = `SUM([New Buyers 30d]) / SUM([New Users])`.
2. Filter **Full Window Observed** = True. Drag **Acquisition Channel** to Rows, **Buyer rate 30d** to Columns. Sort.
3. Title: *Paid social brings the weakest buyers*.

**View 5 · Cohort retention** (data: cohorts)
1. Drag **First Order Month** (as *Month*, discrete) to Rows, **Months Since First Order** (discrete) to Columns.
2. Drag **Retention Rate** to Color and to Label (format as %). Change the mark type to **Square**.
3. Title: *Repeat purchase by first-order cohort*.

## 4. Assemble the dashboard
**Dashboard → New Dashboard**, size **Automatic**. Add a title text box:
*Kroma marketplace: funnel, experiment and retention (synthetic data)*.
Place Views 1 and 3 on the top row, View 2 across the middle, Views 4 and 5 on the bottom row.

## 5. Publish
**File → Save to Tableau Public**, name it *Kroma Marketplace Product Analytics*. Copy the public link and
paste it into the README where it says `TABLEAU_LINK`.
