import geopandas as gpd
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib_scalebar.scalebar import ScaleBar


FOLDER = Path.cwd()

GEOPACKAGES = FOLDER / "GeoPackages"

rivers_raw = gpd.read_file(GEOPACKAGES / "nigerian_rivers.gpkg")
nigerian_states = gpd.read_file(GEOPACKAGES / "nigerian_states.gpkg")
protected_areas_raw = gpd.read_file(GEOPACKAGES / "protected_areas.gpkg")

rivers = rivers_raw[
    ["HYRIV_ID", "LENGTH_KM", "DIS_AV_CMS", "ORD_STRA", "geometry"]
].copy()

rivers = rivers.rename(
    columns={
        "HYRIV_ID": "river_id",
        "LENGTH_KM": "length_km",
        "DIS_AV_CMS": "discharge_cms",
        "ORD_STRA": "stream_order",
    }
)

rivers = rivers.to_crs(epsg=32632)

protected_areas = protected_areas_raw[
    [
        "SITE_ID",
        "NAME_ENG",
        "DESIG_ENG",
        "IUCN_CAT",
        "STATUS",
        "STATUS_YR",
        "GOV_TYPE",
        "GIS_AREA",
        "geometry",
    ]
].copy()

protected_areas = protected_areas.rename(
    columns={
        "SITE_ID": "site_id",
        "NAME_ENG": "site_name",
        "DESIG_ENG": "designation",
        "IUCN_CAT": "iucn_category",
        "STATUS": "status",
        "STATUS_YR": "status_year",
        "GOV_TYPE": "governance",
        "GIS_AREA": "area_km2",
    }
)

protected_areas = protected_areas.to_crs(epsg=32632)

nigerian_states = nigerian_states.to_crs(epsg=32632)

major_rivers = rivers[rivers["stream_order"] >= 5]

#Selecting Kaduna from Nigerian States
kaduna = nigerian_states.query("statename == 'Kaduna'")

#Clipping Rivers and Protected Areas to Kaduna
kaduna_rivers = gpd.clip(major_rivers, kaduna)
kaduna_pas = gpd.clip(protected_areas, kaduna)

# Identify protected areas in Kaduna intersected by major rivers
pa_river_join = gpd.sjoin(
    kaduna_pas,
    kaduna_rivers,
    predicate="intersects",
    how="left",
)

parks_with_rivers = (
    pa_river_join.groupby("site_name")["river_id"]
    .apply(lambda river_ids: river_ids.notna().any())
)

parks_with_rivers = parks_with_rivers[parks_with_rivers]

kaduna_pas["has_river"] = (
    kaduna_pas["site_name"]
    .isin(parks_with_rivers.index)
    .map({True: "Yes", False: "No"})
)

fig, ax = plt.subplots(figsize=(7, 7))

kaduna.plot(color="lightgrey", edgecolor="black", ax=ax, alpha=0.3)
kaduna_rivers.plot(color="blue", linewidth=2, ax=ax)
kaduna_pas.plot(color="green", alpha=0.6, ax=ax)

legend_elements = [
    Patch(facecolor="lightgrey", edgecolor="black", label="Kaduna State"),
    Patch(facecolor="green", edgecolor="green", alpha=0.6, label="Protected Areas"),
    Line2D([0], [0], color="blue", linewidth=1, label="Rivers"),
]

ax.legend(
    handles=legend_elements,
    loc="center left",
    title="Map Features",
    bbox_to_anchor=(0.05, 0.47),
    edgecolor="black",
)

ax.set_axis_off()

ax.set_title(
    "Protected Areas and Rivers in Kaduna State",
    fontdict={"size": 14, "weight": "bold"},
)

scalebar = ScaleBar(
    dx=1,
    units="m",
    scale_loc="bottom",
    location="lower right",
    length_fraction=0.2,
    font_properties={"size": 10},
    box_alpha=0.7,
    box_color="w",
)

ax.add_artist(scalebar)

ax.text(
    0.05,
    0.05,
    "Data Sources:\nWDPA (2025)\nHydroRIVERS\nGRID3",
    transform=ax.transAxes,
    fontdict={"size": 8},
)

# Label protected areas that intersect major rivers
for _, protected_area in kaduna_pas.iterrows():
    if protected_area["has_river"] == "Yes":
        label_point = protected_area.geometry.representative_point()
        ax.text(
            label_point.x,
            label_point.y,
            protected_area["site_name"],
            fontdict={"size": 8},
        )

ax.annotate(
    "N",
    xy=(0.96, 0.96),
    xytext=(0.96, 0.88),
    xycoords="axes fraction",
    arrowprops={
        "facecolor": "w",
        "edgecolor": "black",
        "width": 1,
        "headwidth": 8,
    },
    ha="center",
    fontsize=12,
    fontweight="bold",
)

plt.tight_layout()
plt.savefig(FOLDER / "Kaduna.png", dpi=300)
plt.show()