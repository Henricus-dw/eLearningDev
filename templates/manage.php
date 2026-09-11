<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Submitted Forms</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <link rel="icon" type="image/png" href="/static/professional-logo.png">
    </head>
    <body>
        <div>
            <h2><a href="form">New Form</a></h2>
        </div>
        
        <h1>Completed Moderation Forms</h1>

        <?php
            // Connect to SQLite database
            $db_path = "/var/enroll/instance/students.db"; // Update with actual path
            $conn = new SQLite3($db_path);

            // Check if connection was successful
            if (!$conn) {
                die("Connection failed: " . $conn->lastErrorMsg());
            }

            // Fetch moderation forms
            $sql = "SELECT * FROM moderationforms";
            $results = $conn->query($sql);

            // Display moderation forms
            if ($results) {
                while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
                    echo "<div class='form-body form-manage-block'>
                            <h3>Moderation Form " . $row["studentattemptid"] . "</h3> 
                            <p><span class='bold'>Attempt ID:</span> " . $row["studentattemptid"] . "</p>
                            <p><span class='bold'>Student Name:</span> " . $row["studentname"] . "</p>
                            <p><span class='bold'>Student ID:</span> " . $row["studentid"] . "</p>
                            <p><span class='bold'>Course Name:</span> " . $row["coursename"] . "</p>
                            <p><span class='bold'>Course ID:</span> " . $row["courseid"] . "</p>
                            <p><span class='bold'>Moderator Name:</span> " . $row["moderatorname"] . "</p>
                            <p><span class='bold'>Date Completed:</span> " . $row["coursecompletiondate"] . "</p>
                            <p><span class='bold'>Moderation Date:</span> " . $row["moderationdate"] . "</p>";

                    // Loop through questions
                    for ($i = 1; $i <= 7; $i++) {
                        echo "<div>
                                <p><span class='bold'>Question $i:</span><br>";
                        echo ($row["question$i"] == '1') ? "Yes" : "No";
                        echo "</p></div>";
                    }

                    echo "<div>
                            <p><span class='bold'>Moderator Comments:</span> " . $row["feedback"] . "</p>
                          </div>
                          </div>";
                }
            } else {
                echo "No moderation forms have been submitted yet.";
            }

            // Close database connection
            $conn->close();
        ?>
    </body>
</html>