# Chinook SQLite Database

This workspace contains the Chinook sample database in SQLite format:

- File: `Chinook_Sqlite.sqlite`
- Purpose: sample music store database for SQL practice, joins, aggregations, and filtering
- Source: official Chinook database repository

## Schema Summary

The database has 11 tables:

- `Album`
- `Artist`
- `Customer`
- `Employee`
- `Genre`
- `Invoice`
- `InvoiceLine`
- `MediaType`
- `Playlist`
- `PlaylistTrack`
- `Track`

## Detailed Schema

### `Album`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `AlbumId` | `INTEGER` | No | PK | `PK_Album` |
| `Title` | `NVARCHAR(160)` | No |  |  |
| `ArtistId` | `INTEGER` | No | FK | References `Artist(ArtistId)` |

Primary key:

- `PK_Album` on `AlbumId`

Foreign key:

- `ArtistId` references `Artist(ArtistId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `Artist`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `ArtistId` | `INTEGER` | No | PK | `PK_Artist` |
| `Name` | `NVARCHAR(120)` | Yes |  |  |

Primary key:

- `PK_Artist` on `ArtistId`

### `Customer`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `CustomerId` | `INTEGER` | No | PK | `PK_Customer` |
| `FirstName` | `NVARCHAR(40)` | No |  |  |
| `LastName` | `NVARCHAR(20)` | No |  |  |
| `Company` | `NVARCHAR(80)` | Yes |  |  |
| `Address` | `NVARCHAR(70)` | Yes |  |  |
| `City` | `NVARCHAR(40)` | Yes |  |  |
| `State` | `NVARCHAR(40)` | Yes |  |  |
| `Country` | `NVARCHAR(40)` | Yes |  |  |
| `PostalCode` | `NVARCHAR(10)` | Yes |  |  |
| `Phone` | `NVARCHAR(24)` | Yes |  |  |
| `Fax` | `NVARCHAR(24)` | Yes |  |  |
| `Email` | `NVARCHAR(60)` | No |  |  |
| `SupportRepId` | `INTEGER` | Yes | FK | References `Employee(EmployeeId)` |

Primary key:

- `PK_Customer` on `CustomerId`

Foreign key:

- `SupportRepId` references `Employee(EmployeeId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `Employee`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `EmployeeId` | `INTEGER` | No | PK | `PK_Employee` |
| `LastName` | `NVARCHAR(20)` | No |  |  |
| `FirstName` | `NVARCHAR(20)` | No |  |  |
| `Title` | `NVARCHAR(30)` | Yes |  |  |
| `ReportsTo` | `INTEGER` | Yes | FK | Self-reference to `Employee(EmployeeId)` |
| `BirthDate` | `DATETIME` | Yes |  |  |
| `HireDate` | `DATETIME` | Yes |  |  |
| `Address` | `NVARCHAR(70)` | Yes |  |  |
| `City` | `NVARCHAR(40)` | Yes |  |  |
| `State` | `NVARCHAR(40)` | Yes |  |  |
| `Country` | `NVARCHAR(40)` | Yes |  |  |
| `PostalCode` | `NVARCHAR(10)` | Yes |  |  |
| `Phone` | `NVARCHAR(24)` | Yes |  |  |
| `Fax` | `NVARCHAR(24)` | Yes |  |  |
| `Email` | `NVARCHAR(60)` | Yes |  |  |

Primary key:

- `PK_Employee` on `EmployeeId`

Foreign key:

- `ReportsTo` references `Employee(EmployeeId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `Genre`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `GenreId` | `INTEGER` | No | PK | `PK_Genre` |
| `Name` | `NVARCHAR(120)` | Yes |  |  |

Primary key:

- `PK_Genre` on `GenreId`

### `Invoice`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `InvoiceId` | `INTEGER` | No | PK | `PK_Invoice` |
| `CustomerId` | `INTEGER` | No | FK | References `Customer(CustomerId)` |
| `InvoiceDate` | `DATETIME` | No |  |  |
| `BillingAddress` | `NVARCHAR(70)` | Yes |  |  |
| `BillingCity` | `NVARCHAR(40)` | Yes |  |  |
| `BillingState` | `NVARCHAR(40)` | Yes |  |  |
| `BillingCountry` | `NVARCHAR(40)` | Yes |  |  |
| `BillingPostalCode` | `NVARCHAR(10)` | Yes |  |  |
| `Total` | `NUMERIC(10,2)` | No |  |  |

Primary key:

- `PK_Invoice` on `InvoiceId`

Foreign key:

- `CustomerId` references `Customer(CustomerId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `InvoiceLine`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `InvoiceLineId` | `INTEGER` | No | PK | `PK_InvoiceLine` |
| `InvoiceId` | `INTEGER` | No | FK | References `Invoice(InvoiceId)` |
| `TrackId` | `INTEGER` | No | FK | References `Track(TrackId)` |
| `UnitPrice` | `NUMERIC(10,2)` | No |  |  |
| `Quantity` | `INTEGER` | No |  |  |

Primary key:

- `PK_InvoiceLine` on `InvoiceLineId`

Foreign keys:

- `InvoiceId` references `Invoice(InvoiceId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`
- `TrackId` references `Track(TrackId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `MediaType`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `MediaTypeId` | `INTEGER` | No | PK | `PK_MediaType` |
| `Name` | `NVARCHAR(120)` | Yes |  |  |

Primary key:

- `PK_MediaType` on `MediaTypeId`

### `Playlist`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `PlaylistId` | `INTEGER` | No | PK | `PK_Playlist` |
| `Name` | `NVARCHAR(120)` | Yes |  |  |

Primary key:

- `PK_Playlist` on `PlaylistId`

### `PlaylistTrack`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `PlaylistId` | `INTEGER` | No | PK, FK | Part of composite primary key |
| `TrackId` | `INTEGER` | No | PK, FK | Part of composite primary key |

Primary key:

- `PK_PlaylistTrack` on (`PlaylistId`, `TrackId`)

Foreign keys:

- `PlaylistId` references `Playlist(PlaylistId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`
- `TrackId` references `Track(TrackId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

### `Track`

| Column | Type | Null | Key | Constraints |
| --- | --- | --- | --- | --- |
| `TrackId` | `INTEGER` | No | PK | `PK_Track` |
| `Name` | `NVARCHAR(200)` | No |  |  |
| `AlbumId` | `INTEGER` | Yes | FK | References `Album(AlbumId)` |
| `MediaTypeId` | `INTEGER` | No | FK | References `MediaType(MediaTypeId)` |
| `GenreId` | `INTEGER` | Yes | FK | References `Genre(GenreId)` |
| `Composer` | `NVARCHAR(220)` | Yes |  |  |
| `Milliseconds` | `INTEGER` | No |  |  |
| `Bytes` | `INTEGER` | Yes |  |  |
| `UnitPrice` | `NUMERIC(10,2)` | No |  |  |

Primary key:

- `PK_Track` on `TrackId`

Foreign keys:

- `AlbumId` references `Album(AlbumId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`
- `GenreId` references `Genre(GenreId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`
- `MediaTypeId` references `MediaType(MediaTypeId)` with `ON DELETE NO ACTION ON UPDATE NO ACTION`

## Row Counts

| Table | Rows |
| --- | ---: |
| `Album` | 347 |
| `Artist` | 275 |
| `Customer` | 59 |
| `Employee` | 8 |
| `Genre` | 25 |
| `Invoice` | 412 |
| `InvoiceLine` | 2,240 |
| `MediaType` | 5 |
| `Playlist` | 18 |
| `PlaylistTrack` | 8,715 |
| `Track` | 3,503 |

## Table Purpose

- `Artist`: music artists
- `Album`: albums and their artist mapping
- `Track`: track-level metadata such as name, album, genre, duration, and price
- `Genre`: track genres
- `MediaType`: media format for tracks
- `Playlist` and `PlaylistTrack`: playlists and their track memberships
- `Customer`: customer identity and contact details
- `Employee`: support staff and reporting structure
- `Invoice`: invoice headers with billing and totals
- `InvoiceLine`: invoice line items linked to tracks

## Sample Data

- Artists include entries like `AC/DC`, `Accept`, and `Aerosmith`
- Customers include international records such as `Luís Gonçalves` from Brazil and `Leonie Köhler` from Germany
- Invoices capture billing countries, dates, and totals
- Tracks include title, album, genre, duration in milliseconds, and unit price

## Notes

- This dataset is suitable for the case study because it supports semantic retrieval over a fixed SQL query repository.
- It is small enough for in-memory query execution.
- It does not satisfy the PDF's suggested "10k records" guidance as-is; the largest table here is `PlaylistTrack` with 8,715 rows.
