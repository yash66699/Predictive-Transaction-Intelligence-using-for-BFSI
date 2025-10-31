// Transaction Check Test Suite
// Run these commands in the browser console to test the implementation

console.log("🧪 Transaction Check Test Suite Loaded");
console.log("========================================");

// Test 1: Check if functions are available
function test1_checkFunctions() {
    console.log("\n✅ Test 1: Checking if functions exist...");
    const functions = [
        'checkTransaction',
        'displayEnhancedTransactionResult', 
        'saveToTransactionHistory',
        'loadTransactionHistory'
    ];
    
    functions.forEach(fn => {
        if (typeof window[fn] === 'function') {
            console.log(`   ✓ ${fn} - Available`);
        } else {
            console.error(`   ✗ ${fn} - Missing!`);
        }
    });
}

// Test 2: Check form elements
function test2_checkFormElements() {
    console.log("\n✅ Test 2: Checking form elements...");
    const elements = [
        'transactionAmount',
        'kycVerified',
        'accountAge',
        'channel',
        'transactionDateTime'
    ];
    
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            console.log(`   ✓ ${id} - Found (value: ${el.value || 'empty'})`);
        } else {
            console.error(`   ✗ ${id} - Missing!`);
        }
    });
}

// Test 3: Test API connectivity
async function test3_apiConnectivity() {
    console.log("\n✅ Test 3: Testing API connectivity...");
    try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        console.log('   ✓ API is reachable');
        console.log('   Response:', data);
    } catch (error) {
        console.error('   ✗ API is not reachable:', error.message);
    }
}

// Test 4: Test authentication status
function test4_authStatus() {
    console.log("\n✅ Test 4: Checking authentication status...");
    const user = firebase.auth().currentUser;
    if (user) {
        console.log('   ✓ User authenticated');
        console.log('   Email:', user.email);
        console.log('   UID:', user.uid);
    } else {
        console.warn('   ⚠ No user authenticated');
    }
}

// Test 5: Fill form with sample data
function test5_fillSampleData() {
    console.log("\n✅ Test 5: Filling form with sample data...");
    document.getElementById('transactionAmount').value = '5000';
    document.getElementById('kycVerified').value = 'Yes';
    document.getElementById('accountAge').value = '365';
    document.getElementById('channel').value = 'TRANSFER';
    
    const now = new Date();
    const datetime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    document.getElementById('transactionDateTime').value = datetime;
    
    console.log('   ✓ Form filled with sample data');
    console.log('   Amount: $5000');
    console.log('   KYC: Yes');
    console.log('   Account Age: 365 days');
    console.log('   Channel: TRANSFER');
}

// Test 6: Test transaction history
function test6_checkHistory() {
    console.log("\n✅ Test 6: Checking transaction history...");
    const history = JSON.parse(localStorage.getItem('transactionHistory') || '[]');
    console.log(`   ✓ Found ${history.length} transactions in history`);
    
    if (history.length > 0) {
        console.log('   Latest transaction:');
        console.log('   -', history[0]);
    }
}

// Test 7: Simulate transaction check (mock)
function test7_mockTransaction() {
    console.log("\n✅ Test 7: Testing with mock data...");
    const mockFormData = {
        transaction_amount: 5000,
        kyc_verified: true,
        account_age_days: 365,
        channel: 'TRANSFER',
        timestamp: new Date().toISOString()
    };
    
    const mockResult = {
        transaction_id: 'test-' + Date.now(),
        is_fraud: false,
        fraud_probability: 0.15,
        risk_score: 25,
        reason: 'Transaction appears normal - TEST MODE',
        rules_triggered: [],
        model_version: 'v1.0',
        timestamp: new Date().toISOString()
    };
    
    console.log('   ✓ Mock data created');
    console.log('   Displaying result...');
    displayEnhancedTransactionResult(mockFormData, mockResult);
    saveToTransactionHistory(mockFormData, mockResult);
    console.log('   ✓ Result displayed and saved to history');
}

// Test 8: Clear test data
function test8_clearTestData() {
    console.log("\n✅ Test 8: Clearing test data...");
    const history = JSON.parse(localStorage.getItem('transactionHistory') || '[]');
    const testTransactions = history.filter(t => t.id && t.id.toString().startsWith('test-'));
    
    if (testTransactions.length > 0) {
        const cleaned = history.filter(t => !t.id || !t.id.toString().startsWith('test-'));
        localStorage.setItem('transactionHistory', JSON.stringify(cleaned));
        console.log(`   ✓ Removed ${testTransactions.length} test transactions`);
    } else {
        console.log('   ✓ No test transactions to remove');
    }
}

// Run all tests
async function runAllTests() {
    console.log("\n🚀 Running All Tests...");
    console.log("========================================");
    
    test1_checkFunctions();
    test2_checkFormElements();
    await test3_apiConnectivity();
    test4_authStatus();
    test5_fillSampleData();
    test6_checkHistory();
    test7_mockTransaction();
    
    console.log("\n========================================");
    console.log("✅ All tests completed!");
    console.log("\n📝 Next Steps:");
    console.log("1. Review the results above");
    console.log("2. Click 'Check Transaction' button to test with real API");
    console.log("3. Run test8_clearTestData() to clean up test data");
}

// Quick commands
console.log("\n📋 Available Test Commands:");
console.log("- runAllTests()           : Run all tests");
console.log("- test1_checkFunctions()  : Check if functions exist");
console.log("- test2_checkFormElements(): Check form elements");
console.log("- test3_apiConnectivity() : Test API connection");
console.log("- test4_authStatus()      : Check authentication");
console.log("- test5_fillSampleData()  : Fill form with sample data");
console.log("- test6_checkHistory()    : View transaction history");
console.log("- test7_mockTransaction() : Test with mock data");
console.log("- test8_clearTestData()   : Clear test transactions");
console.log("\n💡 Quick Start: Copy and paste 'runAllTests()' to begin!");
