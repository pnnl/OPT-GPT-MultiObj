import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import BaselineObj
import MultiObjOpt_module


# Title and Description
st.title("Freight Transportation Fuel Optimization Dashboard")
st.write("This dashboard helps optimize fuel allocations for different transport modes (Highway, Rail, Maritime) "
         "based on cost and emissions. Adjust parameters, upload data, and visualize the results.")

# Sidebar Section for Inputs
st.sidebar.header("User Inputs")

# Freight Volumes Input
st.sidebar.subheader("Freight Volumes (Billion ton-miles)")
freight_volume = {
    "Highway": st.sidebar.number_input("Highway Freight Volume", min_value=0.0, value=926.0),
    "Rail": st.sidebar.number_input("Rail Freight Volume", min_value=0.0, value=604.0),
    "Maritime": st.sidebar.number_input("Maritime Freight Volume", min_value=0.0, value=221.0)
}

# Cost Increase Limit
st.sidebar.subheader("Cost Constraints")
max_cost_increase = st.sidebar.slider("Max Cost Increase Allowed (%)", min_value=0, max_value=100, value=20)

# Fuel Options by Mode
st.sidebar.subheader("Select Fuels to Consider")
all_fuels = [
    "petroleum diesel", "e-diesel", "FT biofuels", "FT biofuels CCS", "renewable diesel",
    "hydrogen", "LNG", "electricity", "ammonia"
]

mode_fuel_options = {
    "Highway": st.sidebar.multiselect(
        "Fuels for Highway", options=all_fuels,
        default=["petroleum diesel", "e-diesel", "hydrogen", "renewable diesel", "FT biofuels", "FT biofuels CCS", "LNG", "electricity"]
    ),
    "Rail": st.sidebar.multiselect(
        "Fuels for Rail", options=all_fuels,
        default=["petroleum diesel", "e-diesel", "hydrogen", "renewable diesel", "FT biofuels", "FT biofuels CCS", "LNG", "electricity"]
    ),
    "Maritime": st.sidebar.multiselect(
        "Fuels for Maritime", options=all_fuels,
        default=["petroleum diesel", "LNG", "hydrogen", "ammonia"]
    ),
}

# Editable Tables for LHV, RHO, and Fuel Consumption
st.sidebar.subheader("Edit Fuel Properties (Optional)")

st.sidebar.subheader("LHV values")
# LHV Default Data
LHV_default = {
    "petroleum diesel": {"Highway": 135.56, "Rail": 135.56, "Maritime": 42.8},
    "e-diesel": {"Highway": 135.56, "Rail": 135.56},
    "renewable diesel": {"Highway": 135.56, "Rail": 135.56},
    "FT biofuels": {"Highway": 126.132, "Rail": 126.132},
    "FT biofuels CCS": {"Highway": 130.52, "Rail": 130.52},
    "ammonia": {"Maritime": 18.6},
    "hydrogen": {"Highway": 119.88, "Rail": 119.88, "Maritime": 120},
    "LNG": {"Highway": 22.409, "Rail": 22.409, "Maritime": 45},
    "electricity": {"Highway": 3.6, "Rail": 3.6},
}
LHV_df = pd.DataFrame(LHV_default).T.fillna("N/A")
edited_LHV = st.sidebar.data_editor(LHV_df, width='stretch')

st.sidebar.subheader("RHO values")
# RHO Default Data
RHO_default = {
    "petroleum diesel": {"Highway": 3.25, "Rail": 3.25, "Maritime": 3.25},
    "e-diesel": {"Highway": 3.25, "Rail": 3.25},
    "renewable diesel": {"Highway": 3.25, "Rail": 3.25},
    "FT biofuels": {"Highway": 3.25, "Rail": 3.25},
    "FT biofuels CCS": {"Highway": 3.25, "Rail": 3.25},
    "ammonia": {"Maritime": 2.58},
    "hydrogen": {"Highway": 0.268, "Rail": 0.268, "Maritime": 0.268},
    "LNG": {"Highway": 1.89, "Rail": 1.89, "Maritime": 1.89},
    "electricity": {"Highway": 1, "Rail": 1},
}
RHO_df = pd.DataFrame(RHO_default).T.fillna("N/A")
edited_RHO = st.sidebar.data_editor(RHO_df, width='stretch')

st.sidebar.subheader("Fuel Consumption values")
# Fuel Consumption Default Data
fuel_consumption_default = {
    "petroleum diesel": {"Highway": 0.008, "Rail": 0.00189, "Maritime": 1.08},
    "e-diesel": {"Highway": 0.008, "Rail": 0.00189},
    "renewable diesel": {"Highway": 0.008, "Rail": 0.00189},
    "FT biofuels": {"Highway": 0.008, "Rail": 0.00236},
    "FT biofuels CCS": {"Highway": 0.008, "Rail": 0.00182},
    "hydrogen": {"Highway": 0.009, "Rail": 0.00189, "Maritime": 0.69},
    "LNG": {"Highway": 0.006, "Rail": 0.00108, "Maritime": 1.18},
    "electricity": {"Highway": 0.095, "Rail": 0.0383},
    "ammonia": {"Maritime": 2.5},
}
fuel_consumption_df = pd.DataFrame(fuel_consumption_default).T.fillna("N/A")
edited_fuel_consumption = st.sidebar.data_editor(fuel_consumption_df, width='stretch')

# File Uploads for CSV Data
st.sidebar.subheader("Upload Fuel Data")
prices_data = st.sidebar.file_uploader("Upload Prices CSV", type=["csv"], help="Upload fuel price data")
ghg_data = st.sidebar.file_uploader("Upload Emissions CSV", type=["csv"], help="Upload fuel emissions data")

# Run Optimization Button
if st.sidebar.button("Run Optimization"):
    try:
        # Load user-provided or default datasets
        if prices_data is not None and ghg_data is not None:
            df_prices = pd.read_csv(prices_data)
            df_ghg = pd.read_csv(ghg_data)
        else:
            st.write("**Reading CSV files**")
            df_prices = pd.read_csv("Data/public.task_4.fuels_prices.csv")
            df_ghg = pd.read_csv("Data/public.task_4.fuels_lca_ghg.csv")

        # Baseline Calculation
        st.write("**Calculating Baseline...**")
         # Call the baseline logic of petroleum diesel (assumes BaselineObj.Run exists)
        BaselineOutputs = BaselineObj.Run(df_prices, df_ghg, edited_LHV.to_dict(), edited_RHO.to_dict(), edited_fuel_consumption.to_dict(), freight_volume)
        # The output from BaselineObj includes baseline prices and GHG emissions for highway, rail, and maritime
        highway_base_prices, rail_base_prices, maritime_base_prices, highway_base_ghg, rail_base_ghg, maritime_base_ghg = BaselineOutputs

        # Run Optimization for Highway
        st.write("**Running Optimization for Highway...**")
        highway_results = MultiObjOpt_module.Run(
            df_prices, df_ghg, highway_base_prices, highway_base_ghg,
            edited_LHV.to_dict(), edited_RHO.to_dict(), freight_volume,
            edited_fuel_consumption.to_dict(), max_cost_increase, "Highway", mode_fuel_options
        )

        # Run Optimization for Rail
        st.write("**Running Optimization for Rail...**")
        rail_results = MultiObjOpt_module.Run(
            df_prices, df_ghg, rail_base_prices, rail_base_ghg,
            edited_LHV.to_dict(), edited_RHO.to_dict(), freight_volume,
            edited_fuel_consumption.to_dict(), max_cost_increase, "Rail", mode_fuel_options
        )

        # Run Optimization for Maritime
        st.write("**Running Optimization for Maritime...**")
        maritime_results = MultiObjOpt_module.Run(
            df_prices, df_ghg, maritime_base_prices, maritime_base_ghg,
            edited_LHV.to_dict(), edited_RHO.to_dict(), freight_volume,
            edited_fuel_consumption.to_dict(), max_cost_increase, "Maritime", mode_fuel_options
        )

        # Display Results
        st.success("Optimization Complete!")
        st.header("Optimization Results")

       # Prepare a consolidated DataFrame of results for all modes
        # Flatten allocations and add to results DataFrame
        scenarios_data = []

        # Example: Iterate through highway, rail, and maritime results
        for mode, results in [
            ("Highway", highway_results),
            ("Rail", rail_results),
            ("Maritime", maritime_results)
        ]:
            for scenario, result in results.items():
                if result["allocations"] is not None:
                    # Create a dictionary representing the row for this scenario
                    row = {
                        "Mode": mode,
                        "Scenario": scenario,
                        "Percent GHG Change": result["percent_ghg"],
                        "Percent Cost Change": result["percent_cost"].item()
                    }
                    
                    # Add individual allocation values (e.g., 'Diesel', 'Hydrogen', etc.) as columns
                    for fuel, allocation in result["allocations"].items():
                        row[f"Allocation ({fuel})"] = allocation
                    
                    scenarios_data.append(row)

        # Convert to DataFrame
        results_df = pd.DataFrame(scenarios_data)

        # Separate Scatter Plots for Each Mode
        modes = ["Highway", "Rail", "Maritime"]

        for mode in modes:
            st.subheader(f"Scatter Plot: {mode} - Emissions Change vs Cost Change")
            st.write(f"This scatter plot shows the trade-off between emission changes and cost changes for all scenarios in the {mode} mode.")
            
            # Filter data for the current mode
            mode_data = results_df[results_df["Mode"] == mode]
            allocation_columns = [col for col in mode_data.columns if "Allocation" in col]
            # Create scatter plot
            fig = px.scatter(
                mode_data,
                x="Percent GHG Change",
                y="Percent Cost Change",
                #text="Scenario",  # Show scenario names on hover
                hover_data=["Scenario"] + allocation_columns,  # Add additional data fields
                title=f"{mode} Mode: Emissions vs Cost Changes",
                labels={"Percent GHG Change": "Emissions Change (%)", "Percent Cost Change": "Cost Change (%)"},
                template="plotly_white"
            )
            fig.update_traces(marker=dict(size=10, opacity=0.8), textposition="top center")
            
            # Display the scatter plot in Streamlit
            st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Error during optimization: {e}")
