// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract SierpinskiToken {
    string public constant name = "Władysłaium";
    string public constant symbol = "WŁA";
    uint8 public constant decimals = 18;
    
    // Mathematical constants (approximated for Solidity)
    uint256 private constant GENESIS_SUPPLY = 21000000 * 10**18;
    uint256 private constant BETA_NUMERATOR = 30;
    uint256 private constant BETA_DENOMINATOR = 100;
    uint256 private constant GOLDEN_RATIO = 1618033988749894 * 10**12; // 1.618033988749894
    uint256 private constant EULERS_NUMBER = 2718281828459045 * 10**15; // 2.718281828459045
    uint256 private constant PI_OVER_3 = 1047197551196597 * 10**15; // π/3 ≈ 1.047197551196597
    
    address public owner;
    uint256 public totalSupply;
    uint256 public currentDepth;
    
    AggregatorV3Interface internal priceFeed;
    
    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) private allowances;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event DepthIncreased(uint256 newDepth);
    event TokensBurned(address indexed burner, uint256 amount);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor(address _priceFeed) {
        owner = msg.sender;
        totalSupply = GENESIS_SUPPLY;
        balances[msg.sender] = GENESIS_SUPPLY;
        currentDepth = 0;
        priceFeed = AggregatorV3Interface(_priceFeed);
    }
    
    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }
    
    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "Transfer to zero address");
        
        uint256 burnAmount = (amount * EULERS_NUMBER) / 10**18;
        uint256 transferAmount = amount - burnAmount;
        
        _transfer(msg.sender, to, transferAmount);
        _burn(msg.sender, burnAmount);
        
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        require(allowances[from][msg.sender] >= amount, "Insufficient allowance");
        
        uint256 burnAmount = (amount * EULERS_NUMBER) / 10**18;
        uint256 transferAmount = amount - burnAmount;
        
        _transfer(from, to, transferAmount);
        _burn(from, burnAmount);
        allowances[from][msg.sender] -= amount;
        
        return true;
    }
    
    function approve(address spender, uint256 amount) public returns (bool) {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function increaseDepth() public onlyOwner {
        currentDepth++;
        totalSupply = (totalSupply * (100 - BETA_NUMERATOR)) / BETA_DENOMINATOR;
        emit DepthIncreased(currentDepth);
    }
    
    function calculateDepthTax() public view returns (uint256) {
        if (currentDepth <= 10) return 0;
        uint256 depthDiff = currentDepth - 10;
        return (depthDiff * depthDiff) * 42 * 10**18;
    }
    
    function applyDepthTax() public onlyOwner {
        uint256 taxAmount = calculateDepthTax();
        _burn(owner, taxAmount);
    }
    
    function _transfer(address from, address to, uint256 amount) private {
        require(balances[from] >= amount, "Insufficient balance");
        balances[from] -= amount;
        balances[to] += amount;
        emit Transfer(from, to, amount);
    }
    
    function _burn(address account, uint256 amount) private {
        require(balances[account] >= amount, "Insufficient balance to burn");
        balances[account] -= amount;
        totalSupply -= amount;
        emit TokensBurned(account, amount);
    }
}
