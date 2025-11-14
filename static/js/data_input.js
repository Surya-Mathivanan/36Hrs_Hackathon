function updateUnit() {
  const sourceType = document.getElementById("source_type").value;
  const unitSelect = document.getElementById("unit");

  unitSelect.value = "";

  const unitOptions = {
    electricity: "kWh",
    bus_diesel: "Liters",
    canteen_lpg: "kg",
    waste_landfill: "kg",
  };

  if (sourceType && unitOptions[sourceType]) {
    unitSelect.value = unitOptions[sourceType];
  }
}

document.getElementById("dataForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const formData = {
    date: document.getElementById("date").value,
    source_type: document.getElementById("source_type").value,
    raw_value: parseFloat(document.getElementById("raw_value").value),
    unit: document.getElementById("unit").value,
  };

  fetch("/api/data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  })
    .then((response) => response.json())
    .then((data) => {
      const messageContainer = document.getElementById("messageContainer");

      if (data.message) {
        messageContainer.innerHTML = `
                <div class="success-message">
                    ${data.message}
                </div>
            `;
        document.getElementById("dataForm").reset();
      } else if (data.error) {
        messageContainer.innerHTML = `
                <div class="error-message">
                    ${data.error}
                </div>
            `;
      }

      setTimeout(() => {
        messageContainer.innerHTML = "";
      }, 3000);
    })
    .catch((error) => {
      console.error("Error:", error);
      const messageContainer = document.getElementById("messageContainer");
      messageContainer.innerHTML = `
            <div class="error-message">
                An error occurred while submitting data
            </div>
        `;
    });
});

document.getElementById("date").valueAsDate = new Date();

// CORE FEATURE: Human Population Data Form Handler
const humanForm = document.getElementById("humanDataForm");
if (humanForm) {
  // Set default date to today
  document.getElementById("human_date").valueAsDate = new Date();

  humanForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = {
      date: document.getElementById("human_date").value,
      student_count: parseInt(document.getElementById("student_count").value),
      staff_count: parseInt(document.getElementById("staff_count").value),
    };

    fetch("/api/human_data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        const messageContainer = document.getElementById("humanMessageContainer");

        if (data.message) {
          const details = data.data || {};
          const cumulative = data.cumulative_stats || {};
          messageContainer.innerHTML = `
            <div class="success-message">
              <strong>${data.message}</strong><br>
              <div style="margin-top: 10px; padding: 10px; background: rgba(0, 212, 170, 0.1); border-radius: 5px;">
                <strong>📊 This Day:</strong><br>
                Population: ${details.total_count || 0} people<br>
                CO₂ Emissions: ${details.this_day_emissions_tonnes || 0} tonnes<br>
                <hr style="margin: 10px 0; border-color: rgba(0, 212, 170, 0.3);">
                <strong>🌍 Cumulative Totals:</strong><br>
                Total Emissions: <strong style="color: #00d4aa; font-size: 1.2em;">${cumulative.total_emissions_tonnes || 0} tonnes CO₂</strong><br>
                Total Records: ${cumulative.total_records || 0} days<br>
                Avg Population: ${cumulative.average_population || 0} people<br>
                (${cumulative.average_students || 0} students + ${cumulative.average_staff || 0} staff)
              </div>
            </div>
          `;
          humanForm.reset();
          document.getElementById("human_date").valueAsDate = new Date();
        } else if (data.error) {
          messageContainer.innerHTML = `
            <div class="error-message">
              ${data.error}
            </div>
          `;
        }

        setTimeout(() => {
          messageContainer.innerHTML = "";
        }, 5000);
      })
      .catch((error) => {
        console.error("Error:", error);
        const messageContainer = document.getElementById("humanMessageContainer");
        messageContainer.innerHTML = `
          <div class="error-message">
            An error occurred while submitting population data
          </div>
        `;
      });
  });
}

// CSV Upload handling
const csvInput = document.getElementById("csvFileInput");
if (csvInput) {
  csvInput.addEventListener("change", function (e) {
    const file = e.target.files[0];
    const messageContainer = document.getElementById("csvMessageContainer");
    messageContainer.innerHTML = "";

    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (evt) {
      const text = evt.target.result;
      // Basic CSV parse: split lines and commas
      const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
      if (lines.length < 2) {
        messageContainer.innerHTML = `<div class="error-message">Invalid CSV format.</div>`;
        return;
      }

      const header = lines[0].trim();
      const expectedHeader = "date,source_type,raw_value,unit";
      if (header.toLowerCase() !== expectedHeader) {
        messageContainer.innerHTML = `<div class="error-message">Invalid CSV format.</div>`;
        return;
      }

      const records = [];
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(",").map((c) => c.trim());
        if (cols.length !== 4) {
          messageContainer.innerHTML = `<div class="error-message">Invalid CSV format.</div>`;
          return;
        }
        const [date, source_type, raw_value, unit] = cols;
        // Basic validation
        if (!date || !source_type || !raw_value || !unit) {
          messageContainer.innerHTML = `<div class="error-message">Invalid CSV format.</div>`;
          return;
        }
        const parsedValue = parseFloat(raw_value.replace(/"/g, ""));
        if (isNaN(parsedValue)) {
          messageContainer.innerHTML = `<div class="error-message">Invalid CSV format.</div>`;
          return;
        }

        records.push({ date, source_type, raw_value: parsedValue, unit });
      }

      // Send to server
      fetch("/api/upload_csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records }),
      })
        .then((res) => res.json())
        .then((resp) => {
          if (resp.success) {
            messageContainer.innerHTML = `<div class="success-message">${
              resp.message || "CSV uploaded successfully."
            }</div>`;
            csvInput.value = "";
          } else {
            messageContainer.innerHTML = `<div class="error-message">${
              resp.error || "Invalid CSV format."
            }</div>`;
          }

          setTimeout(() => {
            messageContainer.innerHTML = "";
          }, 5000);
        })
        .catch((err) => {
          console.error(err);
          messageContainer.innerHTML = `<div class="error-message">An error occurred while uploading CSV.</div>`;
        });
    };

    reader.readAsText(file);
  });
}
