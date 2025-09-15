from pyomo.environ import *
import BaselineObj
import MultiObjOpt_module

def calculate_baseline_module(df_prices, df_ghg, freight_volume, LHV, RHO):
    """
    Calculate baseline costs and GHG emissions for petroleum diesel across Highway, Rail, and Maritime.

    Args:
        df_prices (pd.DataFrame): Fuel price data.
        df_ghg (pd.DataFrame): Emissions data.
        freight_volume (dict): Freight volume split between modes.
        LHV (dict): Lower heating value (MJ/kg) for each fuel type.
        RHO (dict): Density (kg/gallon) for each fuel type.

    Returns:
        tuple: Baseline costs and GHG emissions for Highway, Rail, and Maritime modes.
    """
    # Call the baseline logic of petroleum diesel (assumes BaselineObj.Run exists)
    BaselineOutputs = BaselineObj.Run(df_prices, df_ghg, LHV, RHO, freight_volume)

    # The output from BaselineObj includes baseline prices and GHG emissions for highway, rail, and maritime
    highway_base_prices, rail_base_prices, maritime_base_prices, highway_base_ghg, rail_base_ghg, maritime_base_ghg = BaselineOutputs
    
    # Return a tuple of all baseline data
    return highway_base_prices, rail_base_prices, maritime_base_prices, highway_base_ghg, rail_base_ghg, maritime_base_ghg


def optimize_fuel_allocation_module(df_prices, df_ghg, baseline_cost, baseline_ghg, LHV, RHO, freight_volume, fuel_consumption, mode):
    """
    Optimize allocation of freight volume to minimize sector-wide emissions
    while keeping costs under a user-specified limit.

    Args:
        df_prices (pd.DataFrame): Fuel price data.
        df_ghg (pd.DataFrame): Fuel emissions data.
        baseline_cost (dict): Baseline cost for comparison (per scenario).
        baseline_ghg (dict): Baseline emissions for comparison (per scenario).
        LHV (dict): Lower heating values of fuels.
        RHO (dict): Density of fuels.
        freight_volume (dict): Freight volume split.
        fuel_consumption (dict): Fuel consumption profile (in G/mile).
        mode (str): Transportation mode ("Highway", "Rail", "Maritime").

    Returns:
        dict: Dictionary containing optimized allocations, GHG, and costs for each scenario.
    """
     # Call the Multi Objective optimization module 
    MultiObjOutputs = MultiObjOpt_module.Run(df_prices, df_ghg, baseline_cost, baseline_ghg, LHV, RHO, freight_volume, fuel_consumption, mode)

    # The output from MultiObjOpt includes prices and emissions for each scenario for highway, rail, and maritime
    results = MultiObjOutputs
    
    # Return a tuple of all results
    return results