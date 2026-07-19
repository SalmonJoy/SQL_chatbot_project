-- q033: highest value invoices
-- Category: sales
-- Description: Lists the top invoices by total invoice amount.

SELECT InvoiceId AS invoice_id,
       InvoiceDate AS invoice_date,
       BillingCountry AS billing_country,
       ROUND(Total, 2) AS invoice_total
FROM Invoice
ORDER BY Total DESC, InvoiceId ASC
LIMIT 10;
