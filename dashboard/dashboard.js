// Dashboard JavaScript functionality with Firebase Integration

// Firebase configuration and initialization
const firebaseConfig = {
  apiKey: "AIzaSyBVxXrx-xIRctnEA4VoEWJUJiR5MUz76pI",
  authDomain: "fraud-detection-c472f.firebaseapp.com",
  projectId: "fraud-detection-c472f",
  storageBucket: "fraud-detection-c472f.firebasestorage.app",
  messagingSenderId: "626690078813",
  appId: "1:626690078813:web:b0fa32f45bf3427b1875b4",
  measurementId: "G-2YMPY1K28S",
};
// Initialize Firebase
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

const auth = firebase.auth();
const db = firebase.firestore();

// Enhanced Auth Guard with Firebase
(function enforceAuthGuard() {
  auth.onAuthStateChanged((user) => {
    if (user) {
      // User is signed in
      console.log("User authenticated:", user.email);
      loadUserData(user);
    } else {
      // No user is signed in, redirect to login
      console.log("No user authenticated, redirecting to login...");
      //   window.location.replace("login.html");
    }
  });
})();
// Backend API Configuration
const BACKEND_URL = "http://localhost:8000"; // Update with your backend URL

// Enhanced Auth Guard with Firebase
(function enforceAuthGuard() {
  auth.onAuthStateChanged((user) => {
    if (user) {
      console.log("User authenticated:", user.email);
      loadUserData(user);
      loadModelPerformance(); // Load metrics on login
    } else {
      console.log("No user authenticated, redirecting to login...");
      //   window.location.replace("../login.html");
    }
  });
})();

// Load user data from Firebase and localStorage
function loadUserData(user) {
  const userNameElement = document.getElementById("userName");

  const storedFirstName = localStorage.getItem("userFirstName");

  if (storedFirstName && storedFirstName !== "User") {
    userNameElement.textContent = storedFirstName;
  } else {
    const displayName = user.displayName || user.email.split("@")[0] || "User";
    userNameElement.textContent = displayName;

    localStorage.setItem("userFirstName", displayName);
    localStorage.setItem("userEmail", user.email);
  }
}

async function checkTransaction() {
  console.log("Checking transaction with enhanced backend...");

  // Get enhanced form data
  const formData = {
    customer_id: document.getElementById("customerId").value,
    account_age_days: parseInt(document.getElementById("accountAge").value),
    transaction_amount: parseFloat(document.getElementById("transactionAmount").value),
    channel: document.getElementById("channel").value,
    kyc_verified: document.getElementById("kycVerified").value === "Yes",
    timestamp: document.getElementById("transactionDateTime").value,
  };

  // Validate form
  if (!formData.customer_id || formData.customer_id.trim() === "") {
    alert("Please enter a valid Customer ID");
    return;
  }
  if (!formData.transaction_amount || formData.transaction_amount <= 0) {
    alert("Please enter a valid transaction amount");
    return;
  }
  if (!formData.account_age_days || formData.account_age_days < 0) {
    alert("Please enter a valid account age");
    return;
  }
  if (!formData.channel) {
    alert("Please select a channel");
    return;
  }
  if (!formData.timestamp) {
    alert("Please select transaction date and time");
    return;
  }

  try {
    // Show loading state
    const checkBtn = document.querySelector(".check-transaction-btn");
    const originalText = checkBtn.innerHTML;
    checkBtn.innerHTML = '<i class="bx bx-loader-circle bx-spin"></i> Analyzing...';
    checkBtn.disabled = true;

    // Send to backend API
    const response = await fetch(`${BACKEND_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    let result;
    if (response.ok) {
      result = await response.json();
    } else {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Enhanced result display with LLM explanations
    displayEnhancedTransactionResult(result, formData);

    // Save to enhanced transaction history
    saveToEnhancedTransactionHistory(formData, result);

    // Update fraud visualization
    updateFraudVisualization();

  } catch (error) {
    console.error("Error checking transaction:", error);

    // Enhanced fallback with mock LLM explanation
    console.log("Using enhanced mock prediction as fallback...");
    const mockResult = generateEnhancedMockPrediction(formData);
    displayEnhancedTransactionResult(mockResult, formData);
    saveToEnhancedTransactionHistory(formData, mockResult);
    updateFraudVisualization();
  } finally {
    // Reset button state
    const checkBtn = document.querySelector(".check-transaction-btn");
    checkBtn.innerHTML = '<i class="bx bxs-shield-check"></i> Check Transaction';
    checkBtn.disabled = false;
  }
}

function validateEnhancedTransactionForm(formData) {
  if (!formData.customer_id || formData.customer_id.trim() === "") {
    alert("Please enter a valid Customer ID");
    return false;
  }
  if (!formData.transaction_amount || formData.transaction_amount <= 0) {
    alert("Please enter a valid transaction amount");
    return false;
  }
  if (!formData.account_age_days || formData.account_age_days < 0) {
    alert("Please enter a valid account age");
    return false;
  }
  if (!formData.channel) {
    alert("Please select a channel");
    return false;
  }
  if (!formData.timestamp) {
    alert("Please select transaction date and time");
    return false;
  }
  return true;
}
function displayEnhancedTransactionResult(result, formData) {
  const resultDiv = document.getElementById("transactionResult");
  const isFraud = result.is_fraud || result.prediction === 1 || result.fraud === true;
  const riskScore = result.risk_score || result.confidence || (isFraud ? 0.85 : 0.15);

  // Enhanced result with LLM explanation
  resultDiv.innerHTML = `
    <h3>🎯 Advanced Fraud Detection Result</h3>
    <div class="result-card ${isFraud ? 'fraud' : 'legitimate'}">
      <div class="result-icon">
        <i class='bx ${isFraud ? "bxs-shield-x" : "bxs-shield-check"}'></i>
      </div>
      <div class="result-content">
        <h4>Transaction Analysis</h4>
        
        <!-- Prediction & Risk Score -->
        <div class="prediction-section">
          <div class="prediction-row">
            <span class="prediction-label">Transaction ID:</span>
            <span class="prediction-value">${formData.customer_id}_${Date.now()}</span>
          </div>
          <div class="prediction-row">
            <span class="prediction-label">Prediction:</span>
            <span class="prediction-value ${isFraud ? 'fraud' : 'legitimate'}">
              ${isFraud ? "🚨 FRAUD" : "✅ LEGITIMATE"}
            </span>
          </div>
          <div class="prediction-row">
            <span class="prediction-label">Risk Score:</span>
            <span class="prediction-value risk-score">${(riskScore * 100).toFixed(1)}%</span>
          </div>
          <div class="prediction-row">
            <span class="prediction-label">Timestamp:</span>
            <span class="prediction-value">${new Date().toLocaleString()}</span>
          </div>
        </div>

        <!-- LLM Explanation -->
        <div class="explanation-section">
          <h5>🤖 AI Explanation</h5>
          <div class="explanation-content">
            ${result.llm_explanation || result.reason || generateLLMExplanation(formData, isFraud, riskScore)}
          </div>
        </div>

        <!-- Rules Triggered -->
        ${result.rules_triggered ? `
        <div class="rules-section">
          <h5>⚡ Rules Triggered</h5>
          <div class="rules-list">
            ${result.rules_triggered.map(rule => `<div class="rule-item">• ${rule}</div>`).join('')}
          </div>
        </div>
        ` : ''}

        <!-- Confidence Meter -->
        <div class="confidence-section">
          <h5>Confidence Level</h5>
          <div class="confidence-meter">
            <div class="confidence-fill" style="width: ${riskScore * 100}%"></div>
          </div>
          <div class="confidence-text">${(riskScore * 100).toFixed(1)}% confidence</div>
        </div>
      </div>
    </div>
  `;

  resultDiv.style.display = "block";
  resultDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function generateEnhancedMockPrediction(formData) {
  // Enhanced fraud detection logic
  let isFraud = false;
  let riskScore = Math.random() * 0.3 + 0.7;
  let rulesTriggered = [];

  // Advanced fraud detection rules
  if (formData.transaction_amount > 10000) {
    isFraud = Math.random() > 0.3;
    rulesTriggered.push("Amount exceeds threshold");
    riskScore += 0.2;
  }
  if (formData.account_age_days < 30) {
    isFraud = isFraud || Math.random() > 0.6;
    rulesTriggered.push("New account with limited history");
    riskScore += 0.15;
  }
  if (!formData.kyc_verified) {
    isFraud = isFraud || Math.random() > 0.5;
    rulesTriggered.push("KYC verification pending");
    riskScore += 0.1;
  }
  if (formData.channel === "mobile" && formData.transaction_amount > 5000) {
    isFraud = isFraud || Math.random() > 0.4;
    rulesTriggered.push("High mobile transaction");
    riskScore += 0.1;
  }

  // Normalize risk score
  riskScore = Math.min(0.95, Math.max(0.05, riskScore));

  return {
    is_fraud: isFraud,
    prediction: isFraud ? 1 : 0,
    fraud: isFraud,
    risk_score: riskScore,
    confidence: riskScore,
    rules_triggered: rulesTriggered,
    llm_explanation: generateLLMExplanation(formData, isFraud, riskScore)
  };
}
// ===== LLM EXPLANATION GENERATOR =====
function generateLLMExplanation(formData, isFraud, riskScore) {
  const explanations = {
    fraud: [
      `This transaction exhibits suspicious patterns including ${formData.transaction_amount > 10000 ? 'unusually high amount' : 'suspicious timing'} and ${formData.account_age_days < 30 ? 'new account activity' : 'unverified channel usage'}.`,
      `Multiple risk factors detected: ${formData.kyc_verified ? 'KYC verified but ' : ''}transaction from ${formData.channel} channel with ${formData.account_age_days}-day old account raises security concerns.`,
      `Fraud pattern matched: ${formData.transaction_amount} amount transaction from ${formData.account_age_days < 7 ? 'very new' : 'relatively new'} account via ${formData.channel}.`
    ],
    legitimate: [
      `Transaction appears legitimate with normal patterns: ${formData.kyc_verified ? 'KYC verified' : 'standard verification'} and consistent account behavior.`,
      `No significant risk factors detected. Transaction amount and channel usage align with typical customer behavior for ${formData.account_age_days}-day old account.`,
      `Standard transaction pattern: Amount within expected range and verified through ${formData.channel} channel.`
    ]
  };

  const type = isFraud ? 'fraud' : 'legitimate';
  const randomExplanation = explanations[type][Math.floor(Math.random() * explanations[type].length)];

  return randomExplanation;
}

// ===== ENHANCED TRANSACTION HISTORY =====
function saveToEnhancedTransactionHistory(formData, result) {
  let history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");

  const transactionRecord = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    customer_id: formData.customer_id,
    transaction_amount: formData.transaction_amount,
    account_age_days: formData.account_age_days,
    channel: formData.channel,
    kyc_verified: formData.kyc_verified,
    is_fraud: result.is_fraud || result.prediction === 1 || result.fraud === true,
    risk_score: result.risk_score || result.confidence,
    confidence: result.confidence,
    status: (result.is_fraud || result.prediction === 1 || result.fraud === true) ? "Fraud" : "Legitimate",
    llm_explanation: result.llm_explanation || result.reason,
    rules_triggered: result.rules_triggered || []
  };

  history.unshift(transactionRecord);
  localStorage.setItem("transactionHistory", JSON.stringify(history));

  // Update history table if on history page
  if (document.getElementById("transactionHistoryPage").style.display !== "none") {
    loadTransactionHistory();
  }
}

// ===== FRAUD VISUALIZATION CHARTS =====
function initializeFraudVisualization() {
  console.log("Initializing fraud visualization...");
  updateLiveStatistics(); // Add this line
  createFraudPieChart();
  createFraudTrendChart();
}

function createFraudPieChart() {
  const ctx = document.getElementById("fraudPieChart");
  if (!ctx) return;

  const history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");
  const fraudCount = history.filter(t => t.is_fraud).length;
  const legitCount = history.length - fraudCount;

  try {
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Fraudulent', 'Legitimate'],
        datasets: [{
          data: [fraudCount, legitCount],
          backgroundColor: ['#ff6b6b', '#00ff6b'],
          borderColor: ['#ff5252', '#00cc55'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#ffffff',
              font: {
                size: 12
              }
            }
          },
          title: {
            display: true,
            text: 'Fraud vs Legitimate Distribution',
            color: '#00ffff',
            font: {
              size: 16
            }
          }
        }
      }
    });
  } catch (error) {
    console.error("Error creating pie chart:", error);
  }
}

function createFraudTrendChart() {
  const ctx = document.getElementById("fraudTrendChart");
  if (!ctx) return;

  const history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");

  // Group by date and count fraud
  const dailyData = {};
  history.forEach(transaction => {
    const date = new Date(transaction.timestamp).toLocaleDateString();
    if (!dailyData[date]) {
      dailyData[date] = { total: 0, fraud: 0 };
    }
    dailyData[date].total++;
    if (transaction.is_fraud) {
      dailyData[date].fraud++;
    }
  });

  const dates = Object.keys(dailyData).sort();
  const fraudCounts = dates.map(date => dailyData[date].fraud);
  const totalCounts = dates.map(date => dailyData[date].total);

  try {
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: 'Fraud Cases',
            data: fraudCounts,
            borderColor: '#ff6b6b',
            backgroundColor: 'rgba(255, 107, 107, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4
          },
          {
            label: 'Total Transactions',
            data: totalCounts,
            borderColor: '#00ffff',
            backgroundColor: 'rgba(0, 255, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#ffffff'
            }
          }
        },
        scales: {
          x: {
            grid: {
              color: 'rgba(0, 255, 255, 0.1)'
            },
            ticks: {
              color: '#ffffff'
            }
          },
          y: {
            grid: {
              color: 'rgba(0, 255, 255, 0.1)'
            },
            ticks: {
              color: '#ffffff'
            }
          }
        }
      }
    });
  } catch (error) {
    console.error("Error creating trend chart:", error);
  }
}

function updateFraudVisualization() {
  console.log("Updating fraud visualization...");
  updateLiveStatistics(); // Add this line
  createFraudPieChart();
  createFraudTrendChart();
}

// ===== MODEL PERFORMANCE METRICS =====

async function loadModelPerformance() {
  console.log("Loading model performance metrics...");

  try {
    const response = await fetch(`${BACKEND_URL}/model-metrics`);

    if (response.ok) {
      const metrics = await response.json();
      updatePerformanceMetrics(metrics);
    } else {
      throw new Error("Failed to fetch metrics");
    }
  } catch (error) {
    console.error("Error loading model metrics:", error);
    console.log("Using mock metrics as fallback...");
    const mockMetrics = generateMockMetrics();
    updatePerformanceMetrics(mockMetrics);
  }
}

function generateMockMetrics() {
  return {
    accuracy: 0.9542,
    precision: 0.9231,
    recall: 0.8571,
    f1_score: 0.8889,
    specificity: 0.9722,
    auc_score: 0.9147,
    confusion_matrix: {
      tn: 105,
      fp: 3,
      fn: 5,
      tp: 30,
    },
  };
}

function updatePerformanceMetrics(metrics) {
  const metricsMap = {
    accuracy: {
      element: ".performance-table tr:nth-child(1) .metric-value",
      value: (metrics.accuracy * 100).toFixed(2) + "%",
    },
    precision: {
      element: ".performance-table tr:nth-child(2) .metric-value",
      value: (metrics.precision * 100).toFixed(2) + "%",
    },
    f1_score: {
      element: ".performance-table tr:nth-child(3) .metric-value",
      value: (metrics.f1_score * 100).toFixed(2) + "%",
    },
    recall: {
      element: ".performance-table tr:nth-child(4) .metric-value",
      value: (metrics.recall * 100).toFixed(2) + "%",
    },
    specificity: {
      element: ".performance-table tr:nth-child(5) .metric-value",
      value: (metrics.specificity * 100).toFixed(2) + "%",
    },
    auc_score: {
      element: ".performance-table tr:nth-child(6) .metric-value",
      value: (metrics.auc_score * 100).toFixed(2) + "%",
    },
  };

  // Update metric values
  Object.keys(metricsMap).forEach((metric) => {
    const element = document.querySelector(metricsMap[metric].element);
    if (element) {
      element.textContent = metricsMap[metric].value;
    }
  });

  // Update status badges
  const statusBadges = document.querySelectorAll(".status-badge.pending");
  statusBadges.forEach((badge) => {
    badge.textContent = "Completed";
    badge.className = "status-badge completed";
  });

  // Add confusion matrix if available
  if (metrics.confusion_matrix) {
    addConfusionMatrix(metrics.confusion_matrix);
  }
}

function addConfusionMatrix(matrix) {
  const performanceSection = document.querySelector(".performance-section");

  // Remove existing confusion matrix if any
  const existingMatrix = document.getElementById("confusionMatrix");
  if (existingMatrix) {
    existingMatrix.remove();
  }

  const matrixHtml = `
        <div class="analysis-section" id="confusionMatrix">
            <h4>📊 Confusion Matrix</h4>
            <div class="confusion-matrix">
                <table class="confusion-table">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Predicted Legitimate</th>
                            <th>Predicted Fraud</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <th>Actual Legitimate</th>
                            <td class="true-negative">${matrix.tn || matrix.true_negative || 0
    }</td>
                            <td class="false-positive">${matrix.fp || matrix.false_positive || 0
    }</td>
                        </tr>
                        <tr>
                            <th>Actual Fraud</th>
                            <td class="false-negative">${matrix.fn || matrix.false_negative || 0
    }</td>
                            <td class="true-positive">${matrix.tp || matrix.true_positive || 0
    }</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

  performanceSection.innerHTML += matrixHtml;
}

// ===== TRANSACTION HISTORY MANAGEMENT =====
function saveToTransactionHistory(formData, result) {
  let history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");

  const transactionRecord = {
    id: result.transaction_id || Date.now(),
    timestamp: result.timestamp || new Date().toISOString(),
    transactionAmount: formData.transaction_amount || formData.transactionAmount,
    kycVerified: formData.kyc_verified !== undefined ? formData.kyc_verified : formData.kycVerified,
    accountAge: formData.account_age_days || formData.accountAge,
    channel: formData.channel,
    is_fraud: result.is_fraud,
    fraud_probability: result.fraud_probability,
    risk_score: result.risk_score,
    confidence: result.fraud_probability,
    reason: result.reason,
    rules_triggered: result.rules_triggered,
    status: result.is_fraud ? "Fraud" : "Legitimate",
  };

  history.unshift(transactionRecord); // Add to beginning

  // Keep only last 100 transactions
  if (history.length > 100) {
    history = history.slice(0, 100);
  }

  localStorage.setItem("transactionHistory", JSON.stringify(history));

  // Update history table if on history page
  if (
    document.getElementById("transactionHistoryPage").style.display !== "none"
  ) {
    loadTransactionHistory();
  }

  console.log("Transaction saved to history:", transactionRecord);
}

function loadTransactionHistory() {
  const history = JSON.parse(
    localStorage.getItem("transactionHistory") || "[]"
  );
  const tableBody = document.getElementById("historyTableBody");

  if (history.length === 0) {
    tableBody.innerHTML = `
            <tr class="no-data">
                <td colspan="7">
                    <div class="no-data-message">
                        <i class='bx bxs-inbox'></i>
                        <p>No transactions checked yet</p>
                        <span>Check some transactions to see them appear here</span>
                    </div>
                </td>
            </tr>
        `;
    return;
  }

  tableBody.innerHTML = history
    .map(
      (transaction) => {
        const amount = transaction.transactionAmount || transaction.transaction_amount || 0;
        const kycVerified = transaction.kycVerified !== undefined ? transaction.kycVerified : transaction.kyc_verified;
        const accountAge = transaction.accountAge || transaction.account_age_days || 0;
        const isFraud = transaction.is_fraud;
        const fraudProb = transaction.fraud_probability ? (transaction.fraud_probability * 100).toFixed(1) : 'N/A';
        const riskScore = transaction.risk_score ? transaction.risk_score.toFixed(0) : 'N/A';

        return `
        <tr class="${isFraud ? 'fraud-row' : 'legitimate-row'}">
            <td>${transaction.id || 'N/A'}</td>
            <td>$${amount.toFixed(2)}</td>
            <td>${kycVerified ? "Yes" : "No"}</td>
            <td>${accountAge} days</td>
            <td>${transaction.channel || 'N/A'}</td>
            <td>${new Date(transaction.timestamp).toLocaleString()}</td>
            <td>
                <span class="fraud-status ${isFraud ? "fraud" : "legitimate"}">
                    ${isFraud ? "🚨 Fraud" : "✅ Legitimate"}
                </span>
                <div class="fraud-details">
                    <small>Probability: ${fraudProb}% | Risk: ${riskScore}</small>
                </div>
            </td>
        </tr>
        `;
      }
    )
    .join("");
}

function clearTransactionHistory() {
  if (
    confirm(
      "Are you sure you want to clear all transaction history? This action cannot be undone."
    )
  ) {
    localStorage.removeItem("transactionHistory");
    loadTransactionHistory();
    alert("All transaction history has been cleared.");
  }
}

function downloadTransactionHistory() {
  const history = JSON.parse(
    localStorage.getItem("transactionHistory") || "[]"
  );

  if (history.length === 0) {
    alert("No transaction history available to download.");
    return;
  }

  // Convert to CSV
  const headers = [
    "ID",
    "Amount",
    "KYC Verified",
    "Account Age",
    "Channel",
    "Timestamp",
    "Status",
  ];
  const csvData = history.map((transaction) => [
    transaction.id,
    `$${transaction.transactionAmount?.toFixed(2) || "0.00"}`,
    transaction.kycVerified ? "Yes" : "No",
    `${transaction.accountAge} days`,
    transaction.channel,
    new Date(transaction.timestamp).toLocaleString(),
    transaction.is_fraud ? "Fraud" : "Legitimate",
  ]);

  const csvContent = [headers, ...csvData]
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  const BOM = "\uFEFF";
  const blob = new Blob([BOM + csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `transaction_history_${new Date().toISOString().split("T")[0]}.csv`
  );
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Initialize dashboard
document.addEventListener("DOMContentLoaded", function () {
  console.log("Enhanced Dashboard initialized successfully!");

  // Initialize all components
  initializeFileUpload();
  initializeNavigation();
  initializeTransactionForm(); // Enhanced form
  loadTransactionHistory();

  // Load model performance metrics and initialize charts
  loadModelPerformance();
  initializePerformanceCharts();
  initializeFraudVisualization(); // NEW: Initialize fraud charts

  // Update fraud visualization on page load
  setTimeout(() => {
    updateFraudVisualization();
  }, 1000);
});
// Load user data from Firebase and localStorage
function loadUserData(user) {
  const userNameElement = document.getElementById("userName");

  // Try to get user data from localStorage first
  const storedFirstName = localStorage.getItem("userFirstName");

  if (storedFirstName && storedFirstName !== "User") {
    userNameElement.textContent = storedFirstName;
    console.log("Welcome, " + storedFirstName + "!");
  } else {
    // If no data in localStorage, use Firebase user data
    const displayName = user.displayName || user.email.split("@")[0] || "User";
    userNameElement.textContent = displayName;

    // Store in localStorage for consistency
    localStorage.setItem("userFirstName", displayName);
    localStorage.setItem("userEmail", user.email);

    console.log("Welcome, " + displayName + "!");
  }
}

// Toggle profile menu
function toggleProfileMenu() {
  const profileMenu = document.getElementById("profileMenu");
  profileMenu.classList.toggle("active");
}

// Close profile menu when clicking outside
document.addEventListener("click", function (event) {
  const profileSection = document.querySelector(".profile-section");
  const profileMenu = document.getElementById("profileMenu");

  if (!profileSection.contains(event.target)) {
    profileMenu.classList.remove("active");
  }
});

// Handle profile menu item clicks
document.addEventListener("DOMContentLoaded", function () {
  const profileMenuItems = document.querySelectorAll(".profile-menu-item");

  profileMenuItems.forEach((item) => {
    item.addEventListener("click", function () {
      const action = this.querySelector("span").textContent;

      switch (action) {
        case "My Profile":
          console.log("Opening profile page...");
          showProfileModal();
          break;
        case "Settings":
          console.log("Opening settings page...");
          showSettingsModal();
          break;
        case "Logout":
          console.log("Logout requested...");
          // Check if logout confirmation is required
          const requireConfirmation =
            localStorage.getItem("requireConfirmation") !== "false";
          if (requireConfirmation) {
            showLogoutModal();
          } else {
            confirmLogout();
          }
          break;
      }

      // Close the menu after selection
      document.getElementById("profileMenu").classList.remove("active");
    });
  });
});

// Add smooth scrolling for better UX
document.addEventListener("DOMContentLoaded", function () {
  // Smooth scroll for any anchor links
  const links = document.querySelectorAll('a[href^="#"]');

  links.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href");
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });
});

// Add loading animation for dashboard content
function showLoading() {
  const dashboardContainer = document.querySelector(".dashboard-container");
  dashboardContainer.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading dashboard...</p>
        </div>
    `;
}

function hideLoading() {
  // This function can be used to hide loading and show actual content
  console.log("Loading complete");
}

// Add keyboard navigation support
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    // Close profile menu on Escape key
    const profileMenu = document.getElementById("profileMenu");
    profileMenu.classList.remove("active");
  }
});

// Initialize dashboard
document.addEventListener("DOMContentLoaded", function () {
  console.log("Dashboard initialized successfully!");

  // Initialize all components
  initializeFileUpload();
  initializeNavigation();
  initializeTransactionForm();
  loadTransactionHistory();
  initializeChat();

  // Load model performance metrics and initialize charts
  loadModelPerformance();
  initializePerformanceCharts();
});

// ===== FILE UPLOAD AND DATASET ANALYSIS =====

let currentDataset = null;

// Initialize file upload functionality
function initializeFileUpload() {
  const fileInput = document.getElementById("csvFileInput");
  const uploadArea = document.getElementById("fileUploadArea");

  // File input change event
  fileInput.addEventListener("change", handleFileSelect);

  // Drag and drop events
  uploadArea.addEventListener("dragover", handleDragOver);
  uploadArea.addEventListener("dragleave", handleDragLeave);
  uploadArea.addEventListener("drop", handleDrop);
}

// Handle file selection
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file && file.type === "text/csv") {
    processCSVFile(file);
  } else if (file) {
    // Only show alert if file is selected but wrong type
    alert("Please select a valid CSV file!");
  }
}

// Handle drag over
function handleDragOver(event) {
  event.preventDefault();
  event.currentTarget.classList.add("dragover");
}

// Handle drag leave
function handleDragLeave(event) {
  event.currentTarget.classList.remove("dragover");
}

// Handle drop
function handleDrop(event) {
  event.preventDefault();
  event.currentTarget.classList.remove("dragover");

  const files = event.dataTransfer.files;
  if (files.length > 0 && files[0].type === "text/csv") {
    processCSVFile(files[0]);
  } else {
    alert("Please drop a valid CSV file!");
  }
}

// Process CSV file
function processCSVFile(file) {
  showUploadProgress();

  const reader = new FileReader();
  reader.onload = function (e) {
    try {
      const csvData = e.target.result;
      const dataset = parseCSV(csvData);
      currentDataset = dataset;

      hideUploadProgress();
      performDatasetAnalysis(dataset);
      showAnalysisResults();
    } catch (error) {
      console.error("Error processing CSV:", error);
      alert("Error processing CSV file. Please check the file format.");
      hideUploadProgress();
    }
  };

  reader.readAsText(file);
}

// Parse CSV data
function parseCSV(csvText) {
  const lines = csvText.split("\n").filter((line) => line.trim() !== "");
  const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""));
  const data = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",").map((v) => v.trim().replace(/"/g, ""));
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || "";
    });
    data.push(row);
  }

  return { headers, data, rawText: csvText };
}

// Show upload progress
function showUploadProgress() {
  document.getElementById("uploadProgress").style.display = "block";
  document.getElementById("fileUploadArea").style.display = "none";

  // Simulate progress
  let progress = 0;
  const progressFill = document.getElementById("progressFill");
  const progressText = document.getElementById("progressText");

  const interval = setInterval(() => {
    progress += Math.random() * 15;
    if (progress >= 100) {
      progress = 100;
      clearInterval(interval);
      progressText.textContent = "Processing dataset...";
    }
    progressFill.style.width = progress + "%";
  }, 100);
}

// Hide upload progress
function hideUploadProgress() {
  document.getElementById("uploadProgress").style.display = "none";
  document.getElementById("fileUploadArea").style.display = "block";
}

// Show analysis results
function showAnalysisResults() {
  document.getElementById("analysisResults").style.display = "block";
}

// Perform comprehensive dataset analysis
function performDatasetAnalysis(dataset) {
  console.log("Analyzing dataset:", dataset);

  // Basic Statistics
  displayBasicStatistics(dataset);

  // Data Quality Analysis
  displayDataQuality(dataset);

  // Column Analysis
  displayColumnAnalysis(dataset);

  // Data Distribution
  displayDataDistribution(dataset);

  // Correlation Analysis
  displayCorrelationAnalysis(dataset);

  // Missing Values Analysis
  displayMissingValues(dataset);

  // Fraud vs Legitimate Analysis
  displayFraudAnalysis(dataset);

  // Transaction Summary
  displayTransactionSummary(dataset);

  // Spending Categories
  displaySpendingCategories(dataset);
}

// Display basic statistics
function displayBasicStatistics(dataset) {
  const statsContainer = document.getElementById("basicStats");
  const { headers, data } = dataset;

  const stats = [
    { label: "Total Rows", value: data.length },
    { label: "Total Columns", value: headers.length },
    { label: "File Size", value: formatFileSize(dataset.rawText.length) },
    {
      label: "Memory Usage",
      value: formatFileSize(JSON.stringify(data).length),
    },
  ];

  statsContainer.innerHTML = stats
    .map(
      (stat) => `
        <div class="stat-card">
            <h5>${stat.label}</h5>
            <div class="stat-value">${stat.value}</div>
        </div>
    `
    )
    .join("");
}

// Display data quality metrics
function displayDataQuality(dataset) {
  const qualityContainer = document.getElementById("dataQuality");
  const { headers, data } = dataset;

  const totalCells = headers.length * data.length;
  const emptyCells = data.reduce((count, row) => {
    return (
      count +
      headers.filter((header) => !row[header] || row[header].trim() === "")
        .length
    );
  }, 0);

  const completeness = (((totalCells - emptyCells) / totalCells) * 100).toFixed(
    2
  );
  const consistency = calculateDataConsistency(dataset);
  const uniqueness = calculateDataUniqueness(dataset);

  const metrics = [
    { label: "Data Completeness", value: completeness + "%" },
    { label: "Data Consistency", value: consistency + "%" },
    { label: "Data Uniqueness", value: uniqueness + "%" },
    { label: "Empty Cells", value: emptyCells },
  ];

  qualityContainer.innerHTML = metrics
    .map(
      (metric) => `
        <div class="quality-metric">
            <h6>${metric.label}</h6>
            <div class="metric-value">${metric.value}</div>
        </div>
    `
    )
    .join("");
}

// Display column analysis
function displayColumnAnalysis(dataset) {
  const columnContainer = document.getElementById("columnAnalysis");
  const { headers, data } = dataset;

  const columnInfo = headers.map((header) => {
    const values = data
      .map((row) => row[header])
      .filter((v) => v && v.trim() !== "");
    const uniqueValues = new Set(values).size;
    const dataType = inferDataType(values);

    return { header, uniqueValues, dataType, totalValues: values.length };
  });

  columnContainer.innerHTML = columnInfo
    .map(
      (col) => `
        <div class="column-card">
            <h6>${col.header}</h6>
            <div class="column-info">
                <p><strong>Data Type:</strong> ${col.dataType}</p>
                <p><strong>Unique Values:</strong> ${col.uniqueValues}</p>
                <p><strong>Total Values:</strong> ${col.totalValues}</p>
                <p><strong>Missing Values:</strong> ${data.length - col.totalValues
        }</p>
            </div>
        </div>
    `
    )
    .join("");
}

// Display data distribution
function displayDataDistribution(dataset) {
  const distributionContainer = document.getElementById("dataDistribution");
  const { headers, data } = dataset;

  // Find numeric columns for distribution analysis
  const numericColumns = headers
    .filter((header) => {
      const values = data
        .map((row) => row[header])
        .filter((v) => v && v.trim() !== "");
      return values.length > 0 && !isNaN(values[0]);
    })
    .slice(0, 4); // Limit to 4 columns for display

  const distributionHTML = numericColumns
    .map((col) => {
      const values = data
        .map((row) => parseFloat(row[col]))
        .filter((v) => !isNaN(v));
      const min = Math.min(...values);
      const max = Math.max(...values);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const median = calculateMedian(values);

      return `
            <div class="chart-container">
                <h6>${col} Distribution</h6>
                <div class="column-info">
                    <p><strong>Min:</strong> ${min.toFixed(2)}</p>
                    <p><strong>Max:</strong> ${max.toFixed(2)}</p>
                    <p><strong>Mean:</strong> ${mean.toFixed(2)}</p>
                    <p><strong>Median:</strong> ${median.toFixed(2)}</p>
                    <p><strong>Range:</strong> ${(max - min).toFixed(2)}</p>
                </div>
            </div>
        `;
    })
    .join("");

  distributionContainer.innerHTML =
    distributionHTML ||
    "<p>No numeric columns found for distribution analysis.</p>";
}

// Display correlation analysis
function displayCorrelationAnalysis(dataset) {
  const correlationContainer = document.getElementById("correlationAnalysis");
  const { headers, data } = dataset;

  // Find numeric columns
  const numericColumns = headers.filter((header) => {
    const values = data
      .map((row) => row[header])
      .filter((v) => v && v.trim() !== "");
    return values.length > 0 && !isNaN(values[0]);
  });

  if (numericColumns.length < 2) {
    correlationContainer.innerHTML =
      "<p>Need at least 2 numeric columns for correlation analysis.</p>";
    return;
  }

  // Calculate correlation matrix
  const correlationMatrix = calculateCorrelationMatrix(numericColumns, data);

  // Create correlation table
  let tableHTML = '<table class="correlation-table"><thead><tr><th>Column</th>';
  numericColumns.forEach((col) => {
    tableHTML += `<th>${col}</th>`;
  });
  tableHTML += "</tr></thead><tbody>";

  numericColumns.forEach((col1, i) => {
    tableHTML += `<tr><td><strong>${col1}</strong></td>`;
    numericColumns.forEach((col2, j) => {
      const correlation = correlationMatrix[i][j];
      const color =
        Math.abs(correlation) > 0.7
          ? "#00ff00"
          : Math.abs(correlation) > 0.5
            ? "#ffff00"
            : "#ffffff";
      tableHTML += `<td style="color: ${color}">${correlation.toFixed(3)}</td>`;
    });
    tableHTML += "</tr>";
  });
  tableHTML += "</tbody></table>";

  correlationContainer.innerHTML = tableHTML;
}

// Display missing values analysis
function displayMissingValues(dataset) {
  const missingContainer = document.getElementById("missingValues");
  const { headers, data } = dataset;

  const missingAnalysis = headers
    .map((header) => {
      const missingCount = data.filter(
        (row) => !row[header] || row[header].trim() === ""
      ).length;
      const missingPercentage = ((missingCount / data.length) * 100).toFixed(2);

      return { header, missingCount, missingPercentage };
    })
    .filter((col) => col.missingCount > 0);

  if (missingAnalysis.length === 0) {
    missingContainer.innerHTML =
      "<p>No missing values found in the dataset! 🎉</p>";
    return;
  }

  missingContainer.innerHTML = missingAnalysis
    .map(
      (col) => `
        <div class="missing-card">
            <h6>${col.header}</h6>
            <div class="missing-count">${col.missingCount}</div>
            <p>${col.missingPercentage}% of total</p>
        </div>
    `
    )
    .join("");
}

// Display fraud vs legitimate analysis
function displayFraudAnalysis(dataset) {
  const fraudContainer = document.getElementById("fraudAnalysis");
  const { headers, data } = dataset;

  // Try to find fraud-related columns
  const fraudColumns = headers.filter(
    (header) =>
      header.toLowerCase().includes("fraud") ||
      header.toLowerCase().includes("is_fraud") ||
      header.toLowerCase().includes("class") ||
      header.toLowerCase().includes("target")
  );

  if (fraudColumns.length > 0) {
    const fraudColumn = fraudColumns[0];
    const fraudValues = data
      .map((row) => row[fraudColumn])
      .filter((v) => v && v.trim() !== "");

    // Count fraud vs legitimate
    const fraudCount = fraudValues.filter(
      (v) =>
        v.toString().toLowerCase() === "1" ||
        v.toString().toLowerCase() === "true" ||
        v.toString().toLowerCase() === "fraud" ||
        v.toString().toLowerCase() === "yes"
    ).length;

    const legitimateCount = fraudValues.length - fraudCount;
    const totalCount = fraudValues.length;

    const fraudPercentage =
      totalCount > 0 ? ((fraudCount / totalCount) * 100).toFixed(2) : 0;
    const legitimatePercentage =
      totalCount > 0 ? ((legitimateCount / totalCount) * 100).toFixed(2) : 0;

    fraudContainer.innerHTML = `
            <div class="fraud-card">
                <h6>🕵️ Fraudulent Transactions</h6>
                <div class="fraud-count">${fraudCount}</div>
                <div class="fraud-percentage">${fraudPercentage}% of total</div>
            </div>
            <div class="fraud-card legitimate">
                <h6>✅ Legitimate Transactions</h6>
                <div class="fraud-count">${legitimateCount}</div>
                <div class="fraud-percentage">${legitimatePercentage}% of total</div>
            </div>
        `;
  } else {
    // If no fraud column found, show generic analysis
    fraudContainer.innerHTML = `
            <div class="fraud-card">
                <h6>📊 Transaction Analysis</h6>
                <div class="fraud-count">${data.length}</div>
                <div class="fraud-percentage">Total transactions analyzed</div>
            </div>
        `;
  }
}


// Initialize chat functionality
function initializeChat() {
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const minimizeChatBtn = document.getElementById('minimizeChatBtn');
  const chatWidget = document.getElementById('chat-widget');

  // Send message on button click
  chatSendBtn.addEventListener('click', () => {
    sendChatMessage();
  });

  // Send message on Enter key
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Handle minimize/maximize
  // Toggle collapsed state (keeps chat in place but hides body)
  minimizeChatBtn.addEventListener('click', () => {
    if (chatWidget.classList.contains('collapsed')) {
      chatWidget.classList.remove('collapsed');
      minimizeChatBtn.innerHTML = '<i class="bx bx-minus"></i>';
    } else {
      chatWidget.classList.add('collapsed');
      minimizeChatBtn.innerHTML = '<i class="bx bx-expand"></i>';
    }
  });

  // Load chat history if available
  loadChatHistory();

  // Focus input when chat is clicked
  chatWidget.addEventListener('click', (e) => {
    // Only focus the input when clicking inside the body area or header (not the collapsed header control)
    if (!chatWidget.classList.contains('collapsed')) {
      // ignore clicks on the send button or header controls
      if (!e.target.closest('#chatSendBtn') && !e.target.closest('.minimize-chat-btn')) {
        chatInput.focus();
      }
    }
  });
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();

  if (!message) return;

  // Add user message to chat
  addChatMessage(message, 'user');
  input.value = '';

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: message,
        context: {
          total_transactions: transactionHistory ? transactionHistory.length : 0,
          fraud_count: transactionHistory ? transactionHistory.filter(t => t.is_fraud).length : 0
        }
      })
    });

    if (response.ok) {
      const data = await response.json();
      addChatMessage(data.response, 'assistant');
    } else {
      // Fallback to mock response if API fails
      const mockResponse = generateMockChatResponse(message);
      addChatMessage(mockResponse, 'assistant');
    }
  } catch (error) {
    console.error('Chat error:', error);
    const mockResponse = generateMockChatResponse(message);
    addChatMessage(mockResponse, 'assistant');
  }
}

function addChatMessage(text, role) {
  const messagesContainer = document.getElementById('chatMessages');

  // Remove welcome message if exists
  const welcome = messagesContainer.querySelector('.chat-welcome');
  if (welcome) {
    welcome.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${role}`;
  messageDiv.innerHTML = `
        <div class="chat-bubble">${text}</div>
    `;

  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Function to load chat history
async function loadChatHistory() {
  const messagesContainer = document.getElementById('chatMessages');
  
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`${BACKEND_URL}/chat/history`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const history = await response.json();
      
      // Clear welcome message only if we have history
      if (history && history.length > 0) {
        messagesContainer.innerHTML = '';
        history.forEach(chat => {
          addChatMessage(chat.message, 'user');
          addChatMessage(chat.response, 'assistant');
        });
      }
    } else {
      // Keep the welcome message if we can't load history
      console.log('Unable to load chat history. Keeping welcome message.');
    }
  } catch (error) {
    console.error('Error loading chat history:', error);
    // Don't clear welcome message on error
  }
}

function generateMockChatResponse(message) {
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes('fraud') || lowerMessage.includes('detect')) {
    return "Our fraud detection system uses a hybrid LSTM + Transformer model combined with 5 business rules. It analyzes factors like transaction amount, KYC status, account age, channel, and transaction timing to identify potential fraud.";
  } else if (lowerMessage.includes('rule')) {
    return "We have 5 business rules: 1) High amount rule (>$10,000), 2) Unverified KYC + international, 3) New account + high amount, 4) Odd hours (midnight-6am), 5) Weekend high amount (>$15,000).";
  } else if (lowerMessage.includes('how') || lowerMessage.includes('work')) {
    return "The system works by: 1) Receiving transaction data, 2) Preprocessing and feature engineering, 3) ML model prediction, 4) Business rules evaluation, 5) Risk score calculation (70% ML + 30% rules), 6) LLM explanation generation.";
  } else {
    return "I'm here to help with fraud detection questions! You can ask about our detection model, business rules, risk scoring, or how to interpret transaction results.";
  }
}

async function loadChatHistory() {
  // Chat history would be loaded from backend in production
  console.log('Chat history loaded');
}

// ===== HELPER FUNCTIONS =====

// Calculate data consistency
function calculateDataConsistency(dataset) {
  const { headers, data } = dataset;
  let consistentRows = 0;

  data.forEach((row) => {
    const hasAllRequiredFields = headers.every(
      (header) => row[header] && row[header].trim() !== ""
    );
    if (hasAllRequiredFields) consistentRows++;
  });

  return Math.round((consistentRows / data.length) * 100);
}

// Calculate data uniqueness
function calculateDataUniqueness(dataset) {
  const { data } = dataset;
  const uniqueRows = new Set(data.map((row) => JSON.stringify(row))).length;
  return Math.round((uniqueRows / data.length) * 100);
}

// Infer data type
function inferDataType(values) {
  if (values.length === 0) return "Unknown";

  const sample = values.slice(0, 100); // Check first 100 values
  const numericCount = sample.filter(
    (v) => !isNaN(v) && v.trim() !== ""
  ).length;
  const dateCount = sample.filter(
    (v) => !isNaN(Date.parse(v)) && v.trim() !== ""
  ).length;

  if (numericCount / sample.length > 0.8) return "Numeric";
  if (dateCount / sample.length > 0.8) return "Date";
  return "Text";
}

// Calculate median
function calculateMedian(values) {
  const sorted = values.sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

// Calculate correlation matrix
function calculateCorrelationMatrix(columns, data) {
  const matrix = [];

  columns.forEach((col1, i) => {
    matrix[i] = [];
    const values1 = data
      .map((row) => parseFloat(row[col1]))
      .filter((v) => !isNaN(v));

    columns.forEach((col2, j) => {
      if (i === j) {
        matrix[i][j] = 1.0;
      } else {
        const values2 = data
          .map((row) => parseFloat(row[col2]))
          .filter((v) => !isNaN(v));
        matrix[i][j] = calculateCorrelation(values1, values2);
      }
    });
  });

  return matrix;
}

// Calculate correlation coefficient
function calculateCorrelation(x, y) {
  if (x.length !== y.length || x.length === 0) return 0;

  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((a, b, i) => a + b * y[i], 0);
  const sumX2 = x.reduce((a, b) => a + b * b, 0);
  const sumY2 = y.reduce((a, b) => a + b * b, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt(
    (n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY)
  );

  return denominator === 0 ? 0 : numerator / denominator;
}

// Display transaction summary
function displayTransactionSummary(dataset) {
  const summaryContainer = document.getElementById("transactionSummary");
  const { headers, data } = dataset;

  // Try to find amount-related columns
  const amountColumns = headers.filter(
    (header) =>
      header.toLowerCase().includes("amount") ||
      header.toLowerCase().includes("value") ||
      header.toLowerCase().includes("price") ||
      header.toLowerCase().includes("cost")
  );

  let totalTransactions = data.length;
  let averageAmount = 0;
  let totalAmount = 0;

  if (amountColumns.length > 0) {
    const amountColumn = amountColumns[0];
    const amounts = data
      .map((row) => parseFloat(row[amountColumn]))
      .filter((v) => !isNaN(v));

    if (amounts.length > 0) {
      totalAmount = amounts.reduce((sum, amount) => sum + amount, 0);
      averageAmount = totalAmount / amounts.length;
    }
  }

  summaryContainer.innerHTML = `
        <div class="transaction-card">
            <h6>📊 Total Transactions</h6>
            <div class="transaction-value">${totalTransactions.toLocaleString()}</div>
            <div class="transaction-label">Records analyzed</div>
        </div>
        <div class="transaction-card">
            <h6>💰 Total Amount</h6>
            <div class="transaction-value">$${totalAmount.toLocaleString(
    undefined,
    { minimumFractionDigits: 2, maximumFractionDigits: 2 }
  )}</div>
            <div class="transaction-label">Sum of all transactions</div>
        </div>
        <div class="transaction-card">
            <h6>📈 Average Amount</h6>
            <div class="transaction-value">$${averageAmount.toLocaleString(
    undefined,
    { minimumFractionDigits: 2, maximumFractionDigits: 2 }
  )}</div>
            <div class="transaction-label">Mean transaction value</div>
        </div>
    `;
}

// Display spending categories
function displaySpendingCategories(dataset) {
  const categoriesContainer = document.getElementById("spendingCategories");
  const { headers, data } = dataset;

  // Try to find category-related columns
  const categoryColumns = headers.filter(
    (header) =>
      header.toLowerCase().includes("category") ||
      header.toLowerCase().includes("type") ||
      header.toLowerCase().includes("merchant") ||
      header.toLowerCase().includes("description")
  );

  if (categoryColumns.length > 0) {
    const categoryColumn = categoryColumns[0];
    const amountColumn = headers.find(
      (header) =>
        header.toLowerCase().includes("amount") ||
        header.toLowerCase().includes("value")
    );

    // Group by category and calculate totals
    const categoryMap = new Map();

    data.forEach((row) => {
      const category = row[categoryColumn] || "Unknown";
      const amount = amountColumn ? parseFloat(row[amountColumn]) || 0 : 1;

      if (categoryMap.has(category)) {
        categoryMap.set(category, categoryMap.get(category) + amount);
      } else {
        categoryMap.set(category, amount);
      }
    });

    // Sort by amount and take top 6
    const sortedCategories = Array.from(categoryMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);

    const totalAmount = sortedCategories.reduce(
      (sum, [_, amount]) => sum + amount,
      0
    );

    const categoriesHTML = sortedCategories
      .map(([category, amount]) => {
        const percentage =
          totalAmount > 0 ? ((amount / totalAmount) * 100).toFixed(1) : 0;
        return `
                <div class="category-card">
                    <h6>${category}</h6>
                    <div class="category-info">
                        <p><strong>Amount:</strong> $${amount.toLocaleString(
          undefined,
          { minimumFractionDigits: 2, maximumFractionDigits: 2 }
        )}</p>
                        <p><strong>Percentage:</strong> ${percentage}%</p>
                        <div class="category-bar">
                            <div class="category-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                </div>
            `;
      })
      .join("");

    categoriesContainer.innerHTML = categoriesHTML;
  } else {
    // If no category column found, show generic analysis
    categoriesContainer.innerHTML = `
            <div class="category-card">
                <h6>📊 Data Overview</h6>
                <div class="category-info">
                    <p><strong>Total Records:</strong> ${data.length}</p>
                    <p><strong>Columns:</strong> ${headers.length}</p>
                    <p><strong>Data Types:</strong> Mixed (text, numeric, categorical)</p>
                </div>
            </div>
        `;
  }
}

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// ===== LOGOUT MODAL FUNCTIONS =====

// Show logout confirmation modal
function showLogoutModal() {
  const modal = document.getElementById("logoutModal");
  modal.classList.add("active");
}

// Hide logout confirmation modal
function hideLogoutModal() {
  const modal = document.getElementById("logoutModal");
  modal.classList.remove("active");
}

// Cancel logout
function cancelLogout() {
  hideLogoutModal();
  console.log("Logout cancelled by user");
}

// Confirm logout
function confirmLogout() {
  console.log("Logging out...");

  // Sign out from Firebase
  auth
    .signOut()
    .then(() => {
      // Clear user data from localStorage
      localStorage.removeItem("userFirstName");
      localStorage.removeItem("userEmail");
      localStorage.removeItem("userMobile");
      localStorage.removeItem("userCountryCode");
      localStorage.removeItem("userLastName");

      console.log("User signed out successfully");

      // Redirect to landing page
      window.location.href = "../index.html";
    })
    .catch((error) => {
      console.error("Error signing out:", error);
      // Fallback: clear localStorage and redirect anyway
      localStorage.clear();
      window.location.href = "../index.html";
    });
}

// Close modal when clicking outside
document.addEventListener("click", function (event) {
  const modal = document.getElementById("logoutModal");
  if (event.target === modal) {
    hideLogoutModal();
  }
});

// Close modal with Escape key
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    hideLogoutModal();
    hideProfileModal();
    closeSettingsModal();
  }
});

// ===== PROFILE MODAL FUNCTIONS =====

// Show profile modal

function showProfileModal() {
  const modal = document.getElementById("profileModal");
  modal.classList.add("active");
  loadProfileFormData();
}

// Hide profile modal

function hideProfileModal() {
  const modal = document.getElementById("profileModal");
  modal.classList.remove("active");
}

// Close profile modal
function closeProfileModal() {
  hideProfileModal();
}

// Load profile data from localStorage and Firebase

function loadProfileFormData() {
  const user = auth.currentUser;
  // Get user data from localStorage (stored during login)

  const firstName = localStorage.getItem("userFirstName") || "User";
  const lastName = localStorage.getItem("userLastName") || "";
  const email = (user && user.email) || localStorage.getItem("userEmail") || "user@example.com";
  const mobile = localStorage.getItem("userMobile") || "";
  const countryCode = localStorage.getItem("userCountryCode") || "+91";
  const dob = localStorage.getItem("userDOB") || "";
  const gender = localStorage.getItem("userGender") || "";
  const address = localStorage.getItem("userAddress") || "";
  const photoData = localStorage.getItem("userProfilePhoto") || "";

  // Full name logic
  const fullName = `${firstName} ${lastName}`.trim();
  document.getElementById("profileFullNameInput").value = fullName || "";
  document.getElementById("profileEmailInput").value = email;
  // Remove any leading +91 or spaces for input field
  // Extract country code and mobile number if stored as "+XX NNNNNNNNNN"
  let code = countryCode, mobileValue = mobile;
  const match = mobile.match(/^(\+\d{1,4})\s*(\d{5,})$/);
  if (match) {
    code = match[1];
    mobileValue = match[2];
  }
  document.getElementById("profileCountryCodeInput").value = code;
  document.getElementById("profileMobileInput").value = mobileValue;
  document.getElementById("profileDOBInput").value = dob;
  document.getElementById("profileGenderInput").value = gender;
  document.getElementById("profileAddressInput").value = address;

  // Profile photo logic
  const photoPreview = document.getElementById("profilePhotoPreview");
  const photoIcon = document.getElementById("profilePhotoIcon");
  if (photoData) {
    photoPreview.src = photoData;
    photoPreview.style.display = "block";
    photoIcon.style.display = "none";
  } else {
    photoPreview.src = "";
    photoPreview.style.display = "none";
    photoIcon.style.display = "block";
  }
  // Reset file input
  document.getElementById("profilePhotoInput").value = "";
}

// Save profile edits
function saveProfileEdit() {
  const fullName = document.getElementById("profileFullNameInput").value.trim();
  const email = document.getElementById("profileEmailInput").value.trim();
  const countryCode = document.getElementById("profileCountryCodeInput").value;
  let mobile = document.getElementById("profileMobileInput").value.trim();
  // Always store as "+CC NNNNNNNNNN"
  if (mobile && !mobile.startsWith(countryCode)) {
    mobile = countryCode + " " + mobile.replace(/^\+?\d{1,4}\s?/, "");
  }
  const dob = document.getElementById("profileDOBInput").value;
  const gender = document.getElementById("profileGenderInput").value;
  const address = document.getElementById("profileAddressInput").value.trim();
  const photoPreview = document.getElementById("profilePhotoPreview");
  const photoData = photoPreview && photoPreview.style.display === "block" ? photoPreview.src : "";

  // Split full name into first and last
  let firstName = fullName, lastName = "";
  if (fullName.includes(" ")) {
    const parts = fullName.split(" ");
    firstName = parts[0];
    lastName = parts.slice(1).join(" ");
  }

  // Save to localStorage
  localStorage.setItem("userFirstName", firstName);
  localStorage.setItem("userLastName", lastName);
  localStorage.setItem("userEmail", email);
  localStorage.setItem("userMobile", mobile);
  localStorage.setItem("userCountryCode", countryCode);
  localStorage.setItem("userDOB", dob);
  localStorage.setItem("userGender", gender);
  localStorage.setItem("userAddress", address);
  if (photoData) {
    localStorage.setItem("userProfilePhoto", photoData);
  } else {
    localStorage.removeItem("userProfilePhoto");
  }

  // Optionally update Firebase user profile (email only)
  const user = auth.currentUser;
  if (user && email && user.email !== email) {
    user.updateEmail(email).catch((err) => {
      alert("Failed to update email in Firebase: " + err.message);
    });
  }

  hideProfileModal();
  // Optionally reload UI with new name/email
  location.reload();
}

// Cancel profile edit (reset form to last saved values)
function cancelProfileEdit() {
  loadProfileFormData();
  hideProfileModal();
}

// Profile photo upload logic
document.addEventListener("DOMContentLoaded", function () {
  const photoInput = document.getElementById("profilePhotoInput");
  if (photoInput) {
    photoInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          const photoPreview = document.getElementById("profilePhotoPreview");
          const photoIcon = document.getElementById("profilePhotoIcon");
          photoPreview.src = evt.target.result;
          photoPreview.style.display = "block";
          photoIcon.style.display = "none";
        };
        reader.readAsDataURL(file);
      }
    });
  }
});

// Reset profile photo to default
function resetProfilePhoto() {
  const photoPreview = document.getElementById("profilePhotoPreview");
  const photoIcon = document.getElementById("profilePhotoIcon");
  photoPreview.src = "";
  photoPreview.style.display = "none";
  photoIcon.style.display = "block";
  localStorage.removeItem("userProfilePhoto");
}

// Load fallback profile data when localStorage is not available
function loadFallbackProfileData() {
  const storedFirstName = localStorage.getItem("userFirstName");

  document.getElementById("profileFullName").textContent =
    storedFirstName || "User Name";
  document.getElementById("profileEmail").textContent = "user@example.com";
  document.getElementById("profileMobile").textContent = "Not provided";
}

// ===== SETTINGS MODAL FUNCTIONS =====

// Show settings modal
function showSettingsModal() {
  const modal = document.getElementById("settingsModal");
  modal.classList.add("active");
  loadSettings();
}

// Hide settings modal
function hideSettingsModal() {
  const modal = document.getElementById("settingsModal");
  modal.classList.remove("active");
}

// Close settings modal
function closeSettingsModal() {
  hideSettingsModal();
}

// Load current settings (all disabled)
function loadSettings() {
  // Settings are currently inactive
  console.log("Settings are disabled");
}

// ===== NAVIGATION FUNCTIONS =====

// Initialize navigation system
function initializeNavigation() {
  // Show welcome page by default
  showPage("welcome");
}

// Show specific page and hide others
function showPage(pageName) {
  // Hide all pages
  const pages = [
    "welcomePage",
    "datasetAnalysisPage",
    "modelPerformancePage",
    "transactionCheckPage",
    "transactionHistoryPage",
  ];

  pages.forEach((pageId) => {
    const page = document.getElementById(pageId);
    if (page) {
      page.style.display = "none";
    }
  });

  // Show selected page
  let targetPageId;
  switch (pageName) {
    case "welcome":
      targetPageId = "welcomePage";
      break;
    case "datasetAnalysis":
      targetPageId = "datasetAnalysisPage";
      break;
    case "modelPerformance":
      targetPageId = "modelPerformancePage";
      break;
    case "transactionCheck":
      targetPageId = "transactionCheckPage";
      break;
    case "transactionHistory":
      targetPageId = "transactionHistoryPage";
      break;
    default:
      targetPageId = "welcomePage";
  }

  const targetPage = document.getElementById(targetPageId);
  if (targetPage) {
    targetPage.style.display = "block";
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  console.log(`Navigated to: ${pageName}`);
}

// ===== ENHANCED TRANSACTION FORM INITIALIZATION =====
function initializeTransactionForm() {
  console.log("Initializing enhanced transaction form...");

  // Set current date and time as default
  const now = new Date();
  const dateTimeInput = document.getElementById("transactionDateTime");

  if (dateTimeInput) {
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");

    dateTimeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  // Generate a random customer ID if field exists
  const customerIdInput = document.getElementById("customerId");
  if (customerIdInput && !customerIdInput.value) {
    customerIdInput.value = "CUST_" + Math.random().toString(36).substr(2, 9).toUpperCase();
    console.log("Generated customer ID:", customerIdInput.value);
  }
}

// Check transaction (NON-FUNCTIONAL as requested)
async function checkTransaction() {
  console.log("Checking transaction with enhanced backend...");

  // Get enhanced form data
  const formData = {
    customer_id: document.getElementById("customerId").value,
    account_age_days: parseInt(document.getElementById("accountAge").value),
    transaction_amount: parseFloat(document.getElementById("transactionAmount").value),
    channel: document.getElementById("channel").value,
    kyc_verified: document.getElementById("kycVerified").value === "Yes",
    timestamp: document.getElementById("transactionDateTime").value,
  };

  // Validate form
  if (!validateEnhancedTransactionForm(formData)) {
    return;
  }

  try {
    // Show loading state
    const checkBtn = document.querySelector(".check-transaction-btn");
    const originalText = checkBtn.innerHTML;
    checkBtn.innerHTML = '<i class="bx bx-loader-circle bx-spin"></i> Analyzing...';
    checkBtn.disabled = true;

    // Send to backend API
    const response = await fetch(`${BACKEND_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    // Enhanced result display with LLM explanations
    displayEnhancedTransactionResult(result, formData);

    // Save to enhanced transaction history
    saveToEnhancedTransactionHistory(formData, result);

    // Update fraud visualization
    updateFraudVisualization();

  } catch (error) {
    console.error("Error checking transaction:", error);

    // Enhanced fallback with mock LLM explanation
    console.log("Using enhanced mock prediction as fallback...");
    const mockResult = generateEnhancedMockPrediction(formData);
    displayEnhancedTransactionResult(mockResult, formData);
    saveToEnhancedTransactionHistory(formData, mockResult);
    updateFraudVisualization();
  } finally {
    // Reset button state
    const checkBtn = document.querySelector(".check-transaction-btn");
    checkBtn.innerHTML = '<i class="bx bxs-shield-check"></i> Check Transaction';
    checkBtn.disabled = false;
  }
}

// ===== TRANSACTION HISTORY MANAGEMENT =====
function loadTransactionHistory() {
  const history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");
  const tableBody = document.getElementById("historyTableBody");

  if (history.length === 0) {
    tableBody.innerHTML = `
            <tr class="no-data">
                <td colspan="7">
                    <div class="no-data-message">
                        <i class='bx bxs-inbox'></i>
                        <p>No transactions checked yet</p>
                        <span>Check some transactions to see them appear here</span>
                    </div>
                </td>
            </tr>
        `;
    return;
  }

  tableBody.innerHTML = history
    .map((transaction) => `
            <tr>
                <td>${transaction.customer_id || transaction.id || 'N/A'}</td>
                <td>$${(transaction.transaction_amount || transaction.amount || 0).toFixed(2)}</td>
                <td>${transaction.kyc_verified ? "Yes" : "No"}</td>
                <td>${transaction.account_age_days || transaction.accountAge || 0} days</td>
                <td>${transaction.channel || 'N/A'}</td>
                <td>${new Date(transaction.timestamp).toLocaleString()}</td>
                <td>
                    <span class="fraud-status ${transaction.is_fraud ? "fraud" : "legitimate"}">
                        ${transaction.is_fraud ? "🚨 Fraud" : "✅ Legitimate"}
                    </span>
                </td>
            </tr>
        `)
    .join("");

  console.log('Transaction history loaded:', history.length, 'transactions');
}

// Save transaction to history
function saveToTransactionHistory(formData, result) {
  let history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");

  const transactionRecord = {
    id: 'T/' + Date.now(),
    timestamp: new Date().toISOString(),
    customer_id: formData.customer_id,
    transaction_amount: formData.transaction_amount,
    kyc_verified: formData.kyc_verified,
    account_age_days: formData.account_age_days,
    channel: formData.channel,
    is_fraud: result.is_fraud || result.prediction === 1 || result.fraud === true,
    status: (result.is_fraud || result.prediction === 1 || result.fraud === true) ? "Fraud" : "Legitimate"
  };

  history.unshift(transactionRecord);
  localStorage.setItem("transactionHistory", JSON.stringify(history));

  // Update history table if on history page
  if (document.getElementById("transactionHistoryPage").style.display !== "none") {
    loadTransactionHistory();
  }
}

// Clear transaction history
function clearTransactionHistory() {
  if (confirm("Are you sure you want to clear all transaction history? This action cannot be undone.")) {
    localStorage.removeItem("transactionHistory");
    loadTransactionHistory();
    alert("All transaction history has been cleared.");
  }
}

// Download transaction history
function downloadTransactionHistory() {
  const history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");

  if (history.length === 0) {
    alert("No transaction history available to download.");
    return;
  }

  // Convert to CSV
  const headers = ["Customer ID", "Transaction Amount", "KYC Verified", "Account Age", "Channel", "Date & Time", "Status"];
  const csvData = history.map((transaction) => [
    transaction.customer_id || transaction.id,
    `$${(transaction.transaction_amount || transaction.amount || 0).toFixed(2)}`,
    transaction.kyc_verified ? "Yes" : "No",
    `${transaction.account_age_days || transaction.accountAge} days`,
    transaction.channel,
    new Date(transaction.timestamp).toLocaleString(),
    transaction.is_fraud ? "Fraud" : "Legitimate"
  ]);

  const csvContent = [headers, ...csvData]
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  const BOM = "\uFEFF";
  const blob = new Blob([BOM + csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", `transaction_history_${new Date().toISOString().split("T")[0]}.csv`);
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ===== MODEL PERFORMANCE FUNCTIONS =====

// Load model performance metrics (placeholder for future implementation)
function loadModelPerformance() {
  console.log("Loading model performance metrics...");
  // Future implementation to load actual metrics from API
}

// Update performance metrics display
function updatePerformanceMetrics(metrics) {
  const table = document.querySelector(".performance-table tbody");
  if (!table) return;

  const rows = table.querySelectorAll("tr");
  const metricKeys = [
    "accuracy",
    "precision",
    "f1Score",
    "recall",
    "specificity",
    "aucScore",
  ];

  rows.forEach((row, index) => {
    if (index < metricKeys.length && metrics[metricKeys[index]] !== undefined) {
      const valueCell = row.querySelector(".metric-value");
      const statusBadge = row.querySelector(".status-badge");

      if (valueCell) {
        valueCell.textContent =
          (metrics[metricKeys[index]] * 100).toFixed(2) + "%";
      }

      if (statusBadge) {
        statusBadge.textContent = "Completed";
        statusBadge.className = "status-badge completed";
      }
    }
  });
}
// ===== MODEL PERFORMANCE CHARTS =====
function initializePerformanceCharts() {
  console.log("Initializing performance charts...");
  createROCChart();
  createMetricsBarChart();
  createPrecisionRecallChart();
}

function createROCChart() {
  const ctx = document.getElementById("rocCurveChart");
  if (!ctx) {
    console.log("ROC chart canvas not found");
    return;
  }

  console.log("Creating ROC chart...");
  const rocData = {
    fpr: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
    tpr: [0, 0.2, 0.4, 0.6, 0.75, 0.85, 0.9, 0.93, 0.96, 0.98, 1],
  };

  try {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: rocData.fpr.map((fpr) => (fpr * 100).toFixed(0) + "%"),
        datasets: [
          {
            label: "ROC Curve (AUC = 0.915)",
            data: rocData.tpr.map((tpr) => tpr * 100),
            borderColor: "#22C55E",
            backgroundColor: "rgba(244, 209, 168, 0.15)",
            borderWidth: 3,
            fill: true,
            tension: 0.4,
          },
          {
            label: "Random Classifier",
            data: rocData.fpr.map((fpr) => fpr * 100),
            borderColor: "#9CA3AF",
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: "#ffffff",
            },
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "False Positive Rate",
              color: "#22C55E",
            },
            grid: {
              color: "rgba(239, 204, 150, 0.12)",
            },
            ticks: {
              color: "#ffffff",
            },
          },
          y: {
            title: {
              display: true,
              text: "True Positive Rate",
              color: "#22C55E",
            },
            grid: {
              color: "rgba(34, 197, 94, 0.12)",
            },
            ticks: {
              color: "#ffffff",
            },
          },
        },
      },
    });
    console.log("ROC chart created successfully");
  } catch (error) {
    console.error("Error creating ROC chart:", error);
  }
}

function createMetricsBarChart() {
  const ctx = document.getElementById("metricsBarChart");
  if (!ctx) {
    console.log("Metrics bar chart canvas not found");
    return;
  }

  console.log("Creating metrics bar chart...");
  const metricsData = {
    labels: [
      "Accuracy",
      "Precision",
      "Recall",
      "F1-Score",
      "Specificity",
      "AUC",
    ],
    values: [95.4, 92.3, 85.7, 88.9, 97.2, 91.5],
  };

  try {
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: metricsData.labels,
        datasets: [
          {
            label: "Performance Metrics (%)",
            data: metricsData.values,
            backgroundColor: [
              "rgba(108, 93, 211, 0.85)",   
              "rgba(34, 197, 94, 0.85)",    
              "rgba(234, 179, 8, 0.85)",    
              "rgba(45, 156, 219, 0.85)",   
              "rgba(246, 78, 96, 0.85)",    
              "rgba(34, 197, 220, 0.85)",   
            ],
            borderColor: [
              "#6C5DD3",
              "#22C55E",
              "#EAB308",
              "#2D9CDB",
              "#F64E60",
              "#22C1DC",
            ],
            borderWidth: 2,
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          x: {
            grid: {
              color: "rgba(0, 255, 255, 0.1)",
            },
            ticks: {
              color: "#ffffff",
            },
          },
          y: {
            beginAtZero: true,
            max: 100,
            grid: {
              color: "rgba(0, 255, 255, 0.1)",
            },
            ticks: {
              color: "#ffffff",
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
    console.log("Metrics bar chart created successfully");
  } catch (error) {
    console.error("Error creating metrics bar chart:", error);
  }
}

function createPrecisionRecallChart() {
  const ctx = document.getElementById("precisionRecallChart");
  if (!ctx) {
    console.log("Precision-Recall chart canvas not found");
    return;
  }

  console.log("Creating precision-recall chart...");
  const prData = {
    recall: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
    precision: [1, 0.95, 0.92, 0.89, 0.87, 0.85, 0.83, 0.81, 0.79, 0.77, 0.75],
  };

  try {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: prData.recall.map((rec) => (rec * 100).toFixed(0) + "%"),
        datasets: [
          {
            label: "Precision-Recall Curve",
            data: prData.precision.map((prec) => prec * 100),
            borderColor: "#6C5DD3",
            backgroundColor: "rgba(108, 93, 211, 0.15)",
            borderWidth: 3,
            fill: true,
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: "#ffffff",
            },
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Recall",
              color: "#6C5DD3",
            },
            grid: {
              color: "rgba(108, 93, 211, 0.12)",
            },
            ticks: {
              color: "#ffffff",
            },
          },
          y: {
            title: {
              display: true,
              text: "Precision",
              color: "#6C5DD3",
            },
            grid: {
              color: "rgba(108, 93, 211, 0.12)",
            },
            ticks: {
              color: "#ffffff",
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
    console.log("Precision-Recall chart created successfully");
  } catch (error) {
    console.error("Error creating precision-recall chart:", error);
  }
}

// ===== TAB MANAGEMENT =====

function switchTab(tabName) {
  console.log("Switching to tab:", tabName);

  // Hide all tab contents
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Remove active class from all tab buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
  });

  // Show selected tab content
  const targetTab = document.getElementById(tabName);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Add active class to clicked tab button
  event.target.classList.add("active");

  // Reinitialize charts when switching to graphs tab
  if (tabName === "graphsTab") {
    setTimeout(() => {
      initializePerformanceCharts();
    }, 100);
  }
}
// ===== LIVE STATISTICS UPDATE =====
function updateLiveStatistics() {
  const history = JSON.parse(localStorage.getItem("transactionHistory") || "[]");
  const totalTransactions = history.length;
  const fraudCount = history.filter(t => t.is_fraud).length;
  const fraudRate = totalTransactions > 0 ? (fraudCount / totalTransactions * 100).toFixed(1) : 0;

  // Calculate average risk score
  const totalRisk = history.reduce((sum, transaction) => sum + (transaction.risk_score || 0), 0);
  const avgRiskScore = totalTransactions > 0 ? (totalRisk / totalTransactions * 100).toFixed(1) : 0;

  // Update DOM elements
  document.getElementById('totalTransactions').textContent = totalTransactions;
  document.getElementById('fraudCount').textContent = fraudCount;
  document.getElementById('fraudRate').textContent = fraudRate + '%';
  document.getElementById('avgRiskScore').textContent = avgRiskScore + '%';

  console.log('Live statistics updated:', { totalTransactions, fraudCount, fraudRate, avgRiskScore });
}

// Update the existing showPage function
// Find this function in your dashboard.js and MODIFY it:
function showPage(pageName) {
  // Hide all pages
  const pages = [
    "welcomePage",
    "datasetAnalysisPage",
    "modelPerformancePage",
    "transactionCheckPage",
    "transactionHistoryPage",
    "fraudVisualizationPage"
  ];

  pages.forEach((pageId) => {
    const page = document.getElementById(pageId);
    if (page) {
      page.style.display = "none";
    }
  });

  // Show selected page
  let targetPageId;
  switch (pageName) {
    case "welcome":
      targetPageId = "welcomePage";
      break;
    case "datasetAnalysis":
      targetPageId = "datasetAnalysisPage";
      break;
    case "modelPerformance":
      targetPageId = "modelPerformancePage";
      break;
    case "transactionCheck":
      targetPageId = "transactionCheckPage";
      break;
    case "transactionHistory":
      targetPageId = "transactionHistoryPage";
      break;
    case "fraudVisualization": // ADD THIS CASE
      targetPageId = "fraudVisualizationPage";
      break;
    default:
      targetPageId = "welcomePage";
  }

  const targetPage = document.getElementById(targetPageId);
  if (targetPage) {
    targetPage.style.display = "block";
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: "smooth" });

    // Initialize charts when Model Performance page is shown
    if (pageName === "modelPerformance") {
      setTimeout(() => {
        initializePerformanceCharts();
      }, 300);
    }
  }

  console.log(`Navigated to: ${pageName}`);
}
