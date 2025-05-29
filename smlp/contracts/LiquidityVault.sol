// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract LiquidityVault {
    IERC20 public immutable usdtToken;
    address public immutable smlpToken;
    
    struct Commitment {
        uint256 amount;
        uint256 commitmentTime;
        uint256 accessDepth;
    }
    
    mapping(address => Commitment) public commitments;
    uint256 public totalCommitted;
    
    event USDTCommitted(address indexed user, uint256 amount, uint256 accessDepth);
    event USDTReleased(address indexed user, uint256 amount);
    
    constructor(address _usdtAddress, address _smlpAddress) {
        usdtToken = IERC20(_usdtAddress);
        smlpToken = _smlpAddress;
    }
    
    function commitUSDT(uint256 amount) external {
        require(amount >= 13.01 * 10**6, "Minimum commitment is 13.01 USDT");
        
        // Determine access depth based on commitment
        uint256 accessDepth;
        if (amount < 100 * 10**6) {
            accessDepth = 5;
        } else if (amount < 1000 * 10**6) {
            accessDepth = 10;
        } else if (amount < 10000 * 10**6) {
            accessDepth = 15;
        } else {
            accessDepth = 20;
        }
        
        // Transfer USDT to vault
        require(usdtToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        // Record commitment
        commitments[msg.sender] = Commitment({
            amount: amount,
            commitmentTime: block.timestamp,
            accessDepth: accessDepth
        });
        
        totalCommitted += amount;
        emit USDTCommitted(msg.sender, amount, accessDepth);
    }
    
    function releaseUSDT() external {
        Commitment memory commitment = commitments[msg.sender];
        require(commitment.amount > 0, "No commitment found");
        require(block.timestamp > commitment.commitmentTime + 30 days, "Commitment period not ended");
        
        // Return USDT
        require(usdtToken.transfer(msg.sender, commitment.amount), "Transfer failed");
        
        totalCommitted -= commitment.amount;
        delete commitments[msg.sender];
        emit USDTReleased(msg.sender, commitment.amount);
    }
    
    function canMineAtDepth(address user, uint256 depth) external view returns (bool) {
        Commitment memory commitment = commitments[user];
        return commitment.accessDepth >= depth;
    }
}
