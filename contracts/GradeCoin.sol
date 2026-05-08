// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GradeCoin {

   
    string public name     = "GradeCoin";
    string public symbol   = "GRC";
    uint8  public decimals = 18;
    uint256 public totalSupply;


    address public admin;

    // ===== Mappings =====
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ===== Events =====
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Mint(address indexed to, uint256 value);
    event OwnershipTransferred(address indexed oldAdmin, address indexed newAdmin);

    // ===== Constructor =====
    constructor() {
        admin = msg.sender;
    }

    // ===== Modifier =====
    modifier onlyOwner() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    // ===== Admin Functions =====

    // mint: Admin 
    function mint(address to, uint256 amount) public onlyOwner {
        require(to != address(0), "Invalid address");
        require(amount > 0, "Amount must be > 0");

        totalSupply     += amount;
        balanceOf[to]   += amount;

        emit Mint(to, amount);
        emit Transfer(address(0), to, amount);
    }

    // transferOwnership: 
    function transferOwnership(address newAdmin) public onlyOwner {
        require(newAdmin != address(0), "Invalid address");

        emit OwnershipTransferred(admin, newAdmin);
        admin = newAdmin;
    }

    // ===== Batch Mint (Bonus / Advanced) =====
    function batchMint(address[] memory recipients, uint256[] memory amounts) public onlyOwner {
        require(recipients.length == amounts.length, "Arrays length mismatch");

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid address in batch");
            require(amounts[i] > 0, "Amount must be > 0");

            totalSupply             += amounts[i];
            balanceOf[recipients[i]] += amounts[i];

            emit Mint(recipients[i], amounts[i]);
            emit Transfer(address(0), recipients[i], amounts[i]);
        }
    }

    // ===== Normal User Functions =====

    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "Invalid address");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");

        balanceOf[msg.sender] -= amount;
        balanceOf[to]         += amount;

        emit Transfer(msg.sender, to, amount);
        return true;
    }

    // ===== View Functions =====
    function getAdmin() public view returns (address) {
        return admin;
    }
}
