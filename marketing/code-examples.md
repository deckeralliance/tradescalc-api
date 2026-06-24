# TradesCalc API — Code Examples

Complete working code examples for all three TradesCalc API modules via RapidAPI.

> **Authentication:** All examples use RapidAPI headers. Replace `YOUR_RAPIDAPI_KEY` with your actual key from [RapidAPI](https://rapidapi.com).
>
> **Direct access:** You can also call the API directly at `https://tradescalc.dev` using an `X-Api-Key` header instead of RapidAPI headers.

---

## ⚡ Electrical API

**RapidAPI Host:** `tradescalc.p.rapidapi.com`
**RapidAPI Listing:** [rapidapi.com/deckeralliance/api/tradescalc](https://rapidapi.com/deckeralliance/api/tradescalc)

### POST /v1/electrical/ampacity

Look up conductor ampacity from NEC 2023 Table 310.16.

#### cURL

```bash
curl -X POST "https://tradescalc.p.rapidapi.com/v1/electrical/ampacity" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc.p.rapidapi.com" \
  -d '{
    "wire_size": "12",
    "material": "copper",
    "temp_rating": "75"
  }'
```

#### Python

```python
import requests

url = "https://tradescalc.p.rapidapi.com/v1/electrical/ampacity"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc.p.rapidapi.com"
}
payload = {
    "wire_size": "12",
    "material": "copper",
    "temp_rating": "75"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Returns: {"wire_size": "12", "material": "copper", "temp_rating": "75",
#           "ampacity": 25, "nec_reference": "NEC 2023 Table 310.16"}
print(f"{data['wire_size']} AWG {data['material']}: {data['ampacity']}A")
```

#### JavaScript

```javascript
// Look up ampacity for 12 AWG copper at 75°C
const response = await fetch(
  "https://tradescalc.p.rapidapi.com/v1/electrical/ampacity",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc.p.rapidapi.com",
    },
    body: JSON.stringify({
      wire_size: "12",
      material: "copper",
      temp_rating: "75",
    }),
  }
);

const data = await response.json();
console.log(`${data.wire_size} AWG ${data.material}: ${data.ampacity}A`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Look up NEC Table 310.16 ampacity
	payload, _ := json.Marshal(map[string]string{
		"wire_size":   "12",
		"material":    "copper",
		"temp_rating": "75",
	})

	req, _ := http.NewRequest("POST",
		"https://tradescalc.p.rapidapi.com/v1/electrical/ampacity",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Look up NEC Table 310.16 ampacity
uri = URI("https://tradescalc.p.rapidapi.com/v1/electrical/ampacity")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc.p.rapidapi.com"
request.body = {
  wire_size: "12",
  material: "copper",
  temp_rating: "75"
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "#{data['wire_size']} AWG #{data['material']}: #{data['ampacity']}A"
```

---

### POST /v1/electrical/voltage-drop

Calculate voltage drop for a conductor run (NEC 210.19(A) Informational Note).

#### cURL

```bash
curl -X POST "https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc.p.rapidapi.com" \
  -d '{
    "load_amps": 30,
    "voltage": 240,
    "distance_ft": 150,
    "wire_size": "10",
    "material": "copper",
    "phase": "single",
    "conduit_type": "pvc",
    "power_factor": 1.0
  }'
```

#### Python

```python
import requests

url = "https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc.p.rapidapi.com"
}
payload = {
    "load_amps": 30,
    "voltage": 240,
    "distance_ft": 150,
    "wire_size": "10",
    "material": "copper",
    "phase": "single",
    "conduit_type": "pvc",
    "power_factor": 1.0
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Check if the drop exceeds the NEC 3% recommendation
print(f"Voltage drop: {data['voltage_drop_volts']}V ({data['voltage_drop_percent']}%)")
```

#### JavaScript

```javascript
// Calculate voltage drop for a 30A load on 10 AWG copper, 150 ft
const response = await fetch(
  "https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc.p.rapidapi.com",
    },
    body: JSON.stringify({
      load_amps: 30,
      voltage: 240,
      distance_ft: 150,
      wire_size: "10",
      material: "copper",
      phase: "single",
      conduit_type: "pvc",
      power_factor: 1.0,
    }),
  }
);

const data = await response.json();
console.log(`Drop: ${data.voltage_drop_volts}V (${data.voltage_drop_percent}%)`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type VoltageDropRequest struct {
	LoadAmps    float64 `json:"load_amps"`
	Voltage     int     `json:"voltage"`
	DistanceFt  float64 `json:"distance_ft"`
	WireSize    string  `json:"wire_size"`
	Material    string  `json:"material"`
	Phase       string  `json:"phase"`
	ConduitType string  `json:"conduit_type"`
	PowerFactor float64 `json:"power_factor"`
}

func main() {
	req_body := VoltageDropRequest{
		LoadAmps: 30, Voltage: 240, DistanceFt: 150,
		WireSize: "10", Material: "copper", Phase: "single",
		ConduitType: "pvc", PowerFactor: 1.0,
	}
	payload, _ := json.Marshal(req_body)

	req, _ := http.NewRequest("POST",
		"https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Calculate voltage drop — 30A on 10 AWG copper, 150 ft, single-phase 240V
uri = URI("https://tradescalc.p.rapidapi.com/v1/electrical/voltage-drop")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc.p.rapidapi.com"
request.body = {
  load_amps: 30, voltage: 240, distance_ft: 150,
  wire_size: "10", material: "copper", phase: "single",
  conduit_type: "pvc", power_factor: 1.0
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "Drop: #{data['voltage_drop_volts']}V (#{data['voltage_drop_percent']}%)"
```

---

### POST /v1/electrical/conduit-fill

Check NEC conduit fill compliance (Chapter 9, Table 1).

#### cURL

```bash
curl -X POST "https://tradescalc.p.rapidapi.com/v1/electrical/conduit-fill" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc.p.rapidapi.com" \
  -d '{
    "conduit_type": "emt",
    "conduit_size": "3/4",
    "wire_size": "12",
    "wire_count": 6
  }'
```

#### Python

```python
import requests

url = "https://tradescalc.p.rapidapi.com/v1/electrical/conduit-fill"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc.p.rapidapi.com"
}
payload = {
    "conduit_type": "emt",
    "conduit_size": "3/4",
    "wire_size": "12",
    "wire_count": 6
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Check if 6x 12 AWG THHN fits in 3/4" EMT
print(f"Fill: {data['fill_percent']}% — Compliant: {data['compliant']}")
```

#### JavaScript

```javascript
// Check conduit fill — 6x 12 AWG in 3/4" EMT
const response = await fetch(
  "https://tradescalc.p.rapidapi.com/v1/electrical/conduit-fill",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc.p.rapidapi.com",
    },
    body: JSON.stringify({
      conduit_type: "emt",
      conduit_size: "3/4",
      wire_size: "12",
      wire_count: 6,
    }),
  }
);

const data = await response.json();
console.log(`Fill: ${data.fill_percent}% — Compliant: ${data.compliant}`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Check NEC conduit fill — 6x 12 AWG in 3/4" EMT
	payload, _ := json.Marshal(map[string]interface{}{
		"conduit_type": "emt",
		"conduit_size": "3/4",
		"wire_size":    "12",
		"wire_count":   6,
	})

	req, _ := http.NewRequest("POST",
		"https://tradescalc.p.rapidapi.com/v1/electrical/conduit-fill",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Check NEC conduit fill — 6x 12 AWG in 3/4" EMT
uri = URI("https://tradescalc.p.rapidapi.com/v1/electrical/conduit-fill")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc.p.rapidapi.com"
request.body = {
  conduit_type: "emt",
  conduit_size: "3/4",
  wire_size: "12",
  wire_count: 6
}.to_json

response = http.request(request)
puts JSON.parse(response.body)
```

---

## 🔥 Fire API

**RapidAPI Host:** `tradescalc-fire.p.rapidapi.com`
**RapidAPI Listing:** [rapidapi.com/deckeralliance/api/tradescalc-fire](https://rapidapi.com/deckeralliance/api/tradescalc-fire)

### POST /v1/fire/hydrant-flow

Calculate available fire flow at 20 psi residual from hydrant flow test data.

#### cURL

```bash
curl -X POST "https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc-fire.p.rapidapi.com" \
  -d '{
    "static_pressure_psi": 65,
    "residual_pressure_psi": 40,
    "flow_at_residual_gpm": 880
  }'
```

#### Python

```python
import requests

url = "https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc-fire.p.rapidapi.com"
}
payload = {
    "static_pressure_psi": 65,
    "residual_pressure_psi": 40,
    "flow_at_residual_gpm": 880
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Available flow at 20 psi residual pressure
print(f"Available flow: {data['available_flow_at_20psi_gpm']} GPM")
print(f"Flow coefficient: {data['flow_coefficient']}")
```

#### JavaScript

```javascript
// Calculate available fire flow from hydrant test data
const response = await fetch(
  "https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc-fire.p.rapidapi.com",
    },
    body: JSON.stringify({
      static_pressure_psi: 65,
      residual_pressure_psi: 40,
      flow_at_residual_gpm: 880,
    }),
  }
);

const data = await response.json();
console.log(`Available flow: ${data.available_flow_at_20psi_gpm} GPM`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Calculate available fire flow at 20 psi residual
	payload, _ := json.Marshal(map[string]float64{
		"static_pressure_psi":   65,
		"residual_pressure_psi": 40,
		"flow_at_residual_gpm":  880,
	})

	req, _ := http.NewRequest("POST",
		"https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc-fire.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Calculate available fire flow from hydrant test data
uri = URI("https://tradescalc-fire.p.rapidapi.com/v1/fire/hydrant-flow")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc-fire.p.rapidapi.com"
request.body = {
  static_pressure_psi: 65,
  residual_pressure_psi: 40,
  flow_at_residual_gpm: 880
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "Available flow: #{data['available_flow_at_20psi_gpm']} GPM"
```

---

### POST /v1/fire/friction-loss

Calculate Hazen-Williams friction loss through a hose or pipe.

#### cURL

```bash
curl -X POST "https://tradescalc-fire.p.rapidapi.com/v1/fire/friction-loss" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc-fire.p.rapidapi.com" \
  -d '{
    "flow_gpm": 250,
    "hose_diameter_inches": 2.5,
    "length_ft": 400,
    "c_factor": 120
  }'
```

#### Python

```python
import requests

url = "https://tradescalc-fire.p.rapidapi.com/v1/fire/friction-loss"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc-fire.p.rapidapi.com"
}
payload = {
    "flow_gpm": 250,
    "hose_diameter_inches": 2.5,
    "length_ft": 400,
    "c_factor": 120
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Friction loss for 250 GPM through 400 ft of 2.5" hose
print(f"Total friction loss: {data['friction_loss_psi']} psi")
print(f"Per 100 ft: {data['friction_loss_per_100ft']} psi")
```

#### JavaScript

```javascript
// Calculate friction loss — 250 GPM through 400 ft of 2.5" hose
const response = await fetch(
  "https://tradescalc-fire.p.rapidapi.com/v1/fire/friction-loss",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc-fire.p.rapidapi.com",
    },
    body: JSON.stringify({
      flow_gpm: 250,
      hose_diameter_inches: 2.5,
      length_ft: 400,
      c_factor: 120,
    }),
  }
);

const data = await response.json();
console.log(`Friction loss: ${data.friction_loss_psi} psi`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Hazen-Williams friction loss — 250 GPM, 2.5" hose, 400 ft
	payload, _ := json.Marshal(map[string]float64{
		"flow_gpm":             250,
		"hose_diameter_inches": 2.5,
		"length_ft":            400,
		"c_factor":             120,
	})

	req, _ := http.NewRequest("POST",
		"https://tradescalc-fire.p.rapidapi.com/v1/fire/friction-loss",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc-fire.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Hazen-Williams friction loss — 250 GPM, 2.5" hose, 400 ft
uri = URI("https://tradescalc-fire.p.rapidapi.com/v1/fire/friction-loss")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc-fire.p.rapidapi.com"
request.body = {
  flow_gpm: 250,
  hose_diameter_inches: 2.5,
  length_ft: 400,
  c_factor: 120
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "Friction loss: #{data['friction_loss_psi']} psi (#{data['friction_loss_per_100ft']} psi/100ft)"
```

---

## 🏗️ Utility API

**RapidAPI Host:** `tradescalc-utility.p.rapidapi.com`
**RapidAPI Listing:** [rapidapi.com/deckeralliance/api/tradescalc-utility](https://rapidapi.com/deckeralliance/api/tradescalc-utility)

### POST /v1/utility/reliability

Calculate IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI) from outage events.

#### cURL

```bash
curl -X POST "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc-utility.p.rapidapi.com" \
  -d '{
    "outage_events": [
      {"customers_affected": 450, "duration_minutes": 120, "event_date": "2024-07-15"},
      {"customers_affected": 200, "duration_minutes": 45, "event_date": "2024-08-02"},
      {"customers_affected": 1200, "duration_minutes": 90, "event_date": "2024-09-10"}
    ],
    "total_customers_served": 15000,
    "period_description": "Q3 2024"
  }'
```

#### Python

```python
import requests

url = "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc-utility.p.rapidapi.com"
}
payload = {
    "outage_events": [
        {"customers_affected": 450, "duration_minutes": 120, "event_date": "2024-07-15"},
        {"customers_affected": 200, "duration_minutes": 45, "event_date": "2024-08-02"},
        {"customers_affected": 1200, "duration_minutes": 90, "event_date": "2024-09-10"}
    ],
    "total_customers_served": 15000,
    "period_description": "Q3 2024"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# IEEE 1366 reliability indices
print(f"SAIDI: {data['saidi']} min/customer")
print(f"SAIFI: {data['saifi']} interruptions/customer")
print(f"CAIDI: {data['caidi']} min/interruption")
print(f"Total customer-minutes: {data['total_customer_minutes']}")
```

#### JavaScript

```javascript
// Calculate IEEE 1366 reliability indices from Q3 outage data
const response = await fetch(
  "https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc-utility.p.rapidapi.com",
    },
    body: JSON.stringify({
      outage_events: [
        { customers_affected: 450, duration_minutes: 120, event_date: "2024-07-15" },
        { customers_affected: 200, duration_minutes: 45, event_date: "2024-08-02" },
        { customers_affected: 1200, duration_minutes: 90, event_date: "2024-09-10" },
      ],
      total_customers_served: 15000,
      period_description: "Q3 2024",
    }),
  }
);

const data = await response.json();
console.log(`SAIDI: ${data.saidi} | SAIFI: ${data.saifi} | CAIDI: ${data.caidi}`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type OutageEvent struct {
	CustomersAffected int     `json:"customers_affected"`
	DurationMinutes   float64 `json:"duration_minutes"`
	EventDate         string  `json:"event_date,omitempty"`
}

type ReliabilityRequest struct {
	OutageEvents        []OutageEvent `json:"outage_events"`
	TotalCustomersServed int          `json:"total_customers_served"`
	PeriodDescription   string        `json:"period_description,omitempty"`
}

func main() {
	reqBody := ReliabilityRequest{
		OutageEvents: []OutageEvent{
			{CustomersAffected: 450, DurationMinutes: 120, EventDate: "2024-07-15"},
			{CustomersAffected: 200, DurationMinutes: 45, EventDate: "2024-08-02"},
			{CustomersAffected: 1200, DurationMinutes: 90, EventDate: "2024-09-10"},
		},
		TotalCustomersServed: 15000,
		PeriodDescription:    "Q3 2024",
	}
	payload, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST",
		"https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc-utility.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Calculate IEEE 1366 reliability indices from Q3 outage data
uri = URI("https://tradescalc-utility.p.rapidapi.com/v1/utility/reliability")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc-utility.p.rapidapi.com"
request.body = {
  outage_events: [
    { customers_affected: 450, duration_minutes: 120, event_date: "2024-07-15" },
    { customers_affected: 200, duration_minutes: 45, event_date: "2024-08-02" },
    { customers_affected: 1200, duration_minutes: 90, event_date: "2024-09-10" }
  ],
  total_customers_served: 15000,
  period_description: "Q3 2024"
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "SAIDI: #{data['saidi']} | SAIFI: #{data['saifi']} | CAIDI: #{data['caidi']}"
```

---

### POST /v1/utility/outage-cost

Estimate the economic cost of an outage event (DOE ICE methodology).

#### cURL

```bash
curl -X POST "https://tradescalc-utility.p.rapidapi.com/v1/utility/outage-cost" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: tradescalc-utility.p.rapidapi.com" \
  -d '{
    "customers_affected": 2000,
    "duration_hours": 4.0,
    "customer_mix": {
      "residential_pct": 80,
      "commercial_pct": 15,
      "industrial_pct": 5
    }
  }'
```

#### Python

```python
import requests

url = "https://tradescalc-utility.p.rapidapi.com/v1/utility/outage-cost"
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "tradescalc-utility.p.rapidapi.com"
}
payload = {
    "customers_affected": 2000,
    "duration_hours": 4.0,
    "customer_mix": {
        "residential_pct": 80,
        "commercial_pct": 15,
        "industrial_pct": 5
    }
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
# Estimated economic impact of the outage
print(f"Total estimated cost: ${data['estimated_cost_usd']:,.2f}")
print(f"Cost per customer: ${data['cost_per_customer']:,.2f}")
```

#### JavaScript

```javascript
// Estimate outage cost — 2000 customers, 4 hours
const response = await fetch(
  "https://tradescalc-utility.p.rapidapi.com/v1/utility/outage-cost",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
      "X-RapidAPI-Host": "tradescalc-utility.p.rapidapi.com",
    },
    body: JSON.stringify({
      customers_affected: 2000,
      duration_hours: 4.0,
      customer_mix: {
        residential_pct: 80,
        commercial_pct: 15,
        industrial_pct: 5,
      },
    }),
  }
);

const data = await response.json();
console.log(`Estimated cost: $${data.estimated_cost_usd.toLocaleString()}`);
```

#### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	// Estimate outage cost — 2000 customers, 4 hours
	payload, _ := json.Marshal(map[string]interface{}{
		"customers_affected": 2000,
		"duration_hours":     4.0,
		"customer_mix": map[string]float64{
			"residential_pct": 80,
			"commercial_pct":  15,
			"industrial_pct":  5,
		},
	})

	req, _ := http.NewRequest("POST",
		"https://tradescalc-utility.p.rapidapi.com/v1/utility/outage-cost",
		bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-RapidAPI-Key", "YOUR_RAPIDAPI_KEY")
	req.Header.Set("X-RapidAPI-Host", "tradescalc-utility.p.rapidapi.com")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
```

#### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

# Estimate outage cost — 2000 customers, 4 hours
uri = URI("https://tradescalc-utility.p.rapidapi.com/v1/utility/outage-cost")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request["Content-Type"] = "application/json"
request["X-RapidAPI-Key"] = "YOUR_RAPIDAPI_KEY"
request["X-RapidAPI-Host"] = "tradescalc-utility.p.rapidapi.com"
request.body = {
  customers_affected: 2000,
  duration_hours: 4.0,
  customer_mix: {
    residential_pct: 80,
    commercial_pct: 15,
    industrial_pct: 5
  }
}.to_json

response = http.request(request)
data = JSON.parse(response.body)
puts "Estimated cost: $#{data['estimated_cost_usd']}"
puts "Per customer: $#{data['cost_per_customer']}"
```

---

> **Note:** All calculations are for estimation and planning purposes only. Verify results with a licensed professional before use in design or construction.
