-- q014: most expensive tracks
-- Category: products
-- Description: Returns the top 10 most expensive tracks based on their unit price, including the track ID, name, and price.

SELECT [TrackId] AS track_id, [Name] AS track_name, [UnitPrice] AS unit_price FROM [Track] ORDER BY [UnitPrice] DESC LIMIT 10;
