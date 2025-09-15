#start code
def Run(df_prices, df_ghg, LHV, RHO, FC, freight_volume):

    def get_price_values_by_scenario(dataframe):
        """
        Filters the DataFrame for rows where Year = 2050 and reporting_fuel = 'petroleum diesel',
        and then extracts the price_USDperGJ values for each unique scenario using a loop.

        Args:
            df_prices (pd.DataFrame): The input fuel price data containing fuel costs for different scenarios.
            df_ghg (pd.DataFrame): The input fuel ghg emissions data containing emissions for different scenarios
            LHV (dict): Lower heating values of fuels.
            RHO (dict): Density of fuels.
            FC (dict): Fuel consumption profile (in G/mile).
            freight_volume (dict): Freight volume split.

        Returns:
            dict: A dictionary where keys are scenarios and values are price_USDperGJ values.
        """
        # Validate 'petroleum diesel' exists in dataframe
        if 'petroleum diesel' not in dataframe['reporting_fuel'].unique():
            raise ValueError("'petroleum diesel' is not present in df_prices['reporting_fuel']. Check your price data.")
        
        # Filter the DataFrame for Year = 2050 and reporting_fuel = 'petroleum diesel'
        filtered_df = dataframe[(dataframe['year'] == 2050) & (dataframe['reporting_fuel'] == 'petroleum diesel')]
    
        #print(filtered_df)
        # Initialize an empty dictionary to store prices by scenario
        scenario_prices = {}

        # Loop through each unique scenario in the filtered DataFrame
        for scenario in filtered_df['scenario'].unique():
            # Extract the rows corresponding to the current scenario
            scenario_df = filtered_df[filtered_df['scenario'] == scenario]
        
            # Get the price_USDperGJ values for the current scenario
            scenario_prices[scenario] = scenario_df['price_USDperGJ'].tolist()

        return scenario_prices

    def sum_kgCO2e_per_scenario(dataframe):
        """
        Filters the DataFrame for Year = 2050 and reporting_fuel = 'petroleum diesel',
        loops through each unique scenario, and sums up the 'kgCO2e_GJ' values for each scenario.

        Args:
            dataframe (pd.DataFrame): The DataFrame to filter and process.

        Returns:
            dict: A dictionary where the keys are scenarios and the values are the summed kgCO2e_GJ values.
        """
        if 'petroleum diesel' not in dataframe['fuel'].unique():
            raise ValueError("'petroleum diesel' is not present in df_ghg['fuel']. Check your emissions data.")
        # Filter rows with Year = 2050 and reporting_fuel = 'petroleum diesel'
        filtered_df = dataframe[(dataframe['year'] == 2050) & (dataframe['fuel'] == 'petroleum diesel')]
    
        # Initialize an empty dictionary to store the summed values by scenario
        scenario_sums = {}

        # Loop through each unique scenario in the filtered DataFrame
        for scenario in filtered_df['scenario'].unique():
            # Extract rows corresponding to the current scenario
            scenario_df = filtered_df[filtered_df['scenario'] == scenario]
        
            # Sum up the kgCO2e_GJ values for the current scenario
            total_kgCO2e = scenario_df['kgCO2e_GJ'].sum()
        
            # Save the sum into the dictionary
            scenario_sums[scenario] = total_kgCO2e

        return scenario_sums

    # Get the price values grouped by scenario
    result_prices = get_price_values_by_scenario(df_prices)

    highway_prices = {} # initialize an empty dictionary to store the highway(truck) freight cost prices for each scenario
    rail_prices = {}  # initialize an empty dictionary to store the rail freight cost prices for each scenario
    maritime_prices = {} # initialize an empty dictionary to store the maritime freight cost prices for each scenario
    # Loop through each scenario to calculate prices for freight truck and rail and maritime
    for scenario, prices in result_prices.items():
        # highway_prices[scenario] = prices[0] * float(RHO['Highway']['petroleum diesel']) * (float(LHV['Highway']['petroleum diesel'])/1000) * 2.636e-2 * float(freight_volume['Highway']) # GCAM price ($/GJ) * GJ/gallon * Billion ton-miles * gallons/ton-mile = $B
        highway_prices[scenario] = prices[0] * (float(LHV['Highway']['petroleum diesel'])/1000) * (float(FC['Highway']['petroleum diesel'])) * float(freight_volume['Highway']) # GCAM price($/GJ) * LHV(GJ/gal) * FC(gal/ton-mile) * Billion ton-miles = $B
        #rail_prices[scenario] = prices[0] * float(RHO['Rail']['petroleum diesel']) * (float(LHV['Rail']['petroleum diesel'])/1000) * 2.636e-2 * float(freight_volume['Rail']) # GCAM price ($/GJ) * GJ/gallon * Billion ton-miles * gallons/ton-mile = $B
        rail_prices[scenario] = prices[0] * (float(LHV['Rail']['petroleum diesel'])/1000) * (float(FC['Rail']['petroleum diesel'])) * float(freight_volume['Rail']) # GCAM price ($/GJ) * LHV(GJ/gal) * FC(gal/ton-mile) * Billion ton-miles = $B
        fuel_prices = prices[0] * float(RHO['Maritime']['petroleum diesel']) * (float(LHV['Maritime']['petroleum diesel'])/1000) # GCAM price ($/GJ) * GJ/gallon
        maritime_prices[scenario] = 0.01*(2.636e-2 * fuel_prices + 8.841e-3 * 27.34 + 4.47e-6 * 287331 + 1.0411)* float(freight_volume['Maritime']) # $B
        
        # highway_prices[scenario] = prices[0] * 0.001205 * 926.43318 # multiplying with GJ/ton-mile and freight truck volume ($B)
        # rail_prices[scenario] = prices[0] * 0.000275 * 604.510158 # multiplying with GJ/ton-mile and freight rail volume ($B)
        # maritime_prices[scenario] =prices[0] *                    # multiplying with GJ/ton-mile and freight maritime volume ($B)

    # Get the summed `kgCO2e_GJ` values for each scenario
    result_ghg = sum_kgCO2e_per_scenario(df_ghg)

    highway_ghg = {} # initialize an empty dictionary to store the highway(truck) freight emissions for each scenario
    rail_ghg = {}  # initialize an empty dictionary to store the rail freight emissions for each scenario
    maritime_ghg = {} # initialize an empty dictionary to store the maritime freight emissions for each scenario

    # Loop through each scenario to calculate emissions for freight truck and rail and maritime
    for scenario, ghg in result_ghg.items():
        #highway_ghg[scenario] = ghg * (float(LHV['Highway']['petroleum diesel'])/1000) * 20 * float(freight_volume['Highway']) # multiplying with GJ/ton-mile and freight truck volume (million ton CO2eq)
        highway_ghg[scenario] = ghg * (float(LHV['Highway']['petroleum diesel'])/1000) * (float(FC['Highway']['petroleum diesel'])) * float(freight_volume['Highway']) # GCAM(kgCO2eq/GJ) * LHV(GJ/gal) * FC(gal/ton-miles) * volume(billion ton-miles) = billion kgCO2eq
        #rail_ghg[scenario] = ghg * (float(LHV['Rail']['petroleum diesel'])/1000) * 6 * float(freight_volume['Rail']) # multiplying with GJ/ton-mile and freight rail volume (million ton CO2eq)
        rail_ghg[scenario] = ghg * (float(LHV['Rail']['petroleum diesel'])/1000) * (float(FC['Rail']['petroleum diesel']))  * float(freight_volume['Rail']) #GCAM(kgCO2eq/GJ) * LHV(GJ/gal) * FC(gal/ton-miles) * volume(billion ton-miles) = billion kgCO2eq
        maritime_ghg[scenario] = ghg * (float(LHV['Maritime']['petroleum diesel'])/1000) * (float(FC['Maritime']['petroleum diesel'])/1000) * float(freight_volume['Maritime'])  # GCAM emissions (KgCO2eq/GJ) * GJ/ton-mile * Billion ton-miles = million kgCO2eq

    return (highway_prices, rail_prices, maritime_prices, highway_ghg, rail_ghg, maritime_ghg)

#end code