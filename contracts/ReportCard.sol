// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReportCard {

    // ═══════════════════════════════════════════════
    //  STATE VARIABLES
    // ═══════════════════════════════════════════════

    address public owner;  // admin wallet
    bool    public paused; // emergency switch

    struct Student {
        string  name;
        uint256 grade;
        bool    isRegistered; // blocks duplicate registration
        bool    hasGrade;     // false until admin assigns a grade
    }

    mapping(address => Student) private students; // main database
    address[] private studentList;                // needed to loop over all students


    
    