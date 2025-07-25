let circles = [];
const numCircles = 80;
let specialCircle;
let centerX, centerY; // Center coordinates for the bunch

function setup() {
  createCanvas(windowWidth, windowHeight);

  // Center of the canvas
  centerX = width / 2;
  centerY = height / 2;

  // Create special circle at center
  specialCircle = new SpecialCircle(
    centerX,
    centerY,
    120,
    color(255, 100, 150)
  );

  // Create regular circles in a bunch around the special circle
  for (let i = 0; i < numCircles; i++) {
    // Random position within a radius around the special circle
    let angle = random(TWO_PI);
    let radius = random(150, 300);
    let x = centerX + cos(angle) * radius;
    let y = centerY + sin(angle) * radius;

    circles.push(new Circle(
      x, y,
      random(60, 120),
      color(random(100, 255), random(100, 200), random(150, 255), 180)
    ));
  }
}

function draw() {
  background(240, 240, 250, 30);

  // Draw special circle first (underneath others)
  specialCircle.update();
  specialCircle.display();

  // Update and display regular circles
  for (let circle of circles) {
    // Make circles attracted to special circle when mouse is far
    if (!mouseIsPressed) {
      circle.attractToSpecial(specialCircle);
    }
    circle.update();
    circle.display();
  }
}

class Circle {
  constructor(x, y, size, color) {
    this.x = x;
    this.y = y;
    this.targetX = x;
    this.targetY = y;
    this.vx = 0; // Velocity x
    this.vy = 0; // Velocity y
    this.size = size;
    this.color = color;
    this.speed = random(0.03, 0.08);
    this.maxForce = random(5, 12); // Stronger repulsion
    this.friction = 0.95; // Friction to slow down velocity gradually
  }

  attractToSpecial(specialCircle) {
    // Calculate vector toward special circle
    let dx = specialCircle.x - this.x;
    let dy = specialCircle.y - this.y;
    let distance = sqrt(dx * dx + dy * dy);

    // Apply attraction force toward special circle
    if (distance > specialCircle.size / 2 + this.size / 2) {
      let strength = 0.01; // Attraction strength
      this.vx += dx * strength;
      this.vy += dy * strength;
    }
  }

  update() {
    // Apply mouse repulsion
    let d = dist(mouseX, mouseY, this.x, this.y);
    let repulsionRadius = 100 + this.size;

    if (d < repulsionRadius) {
      // Calculate repulsion force
      let angle = atan2(this.y - mouseY, this.x - mouseX);
      let force = map(d, 0, repulsionRadius, this.maxForce, 0);

      // Apply repulsion as velocity
      this.vx += cos(angle) * force;
      this.vy += sin(angle) * force;
    }

    // Apply velocity
    this.x += this.vx;
    this.y += this.vy;

    // Apply friction to gradually slow down
    this.vx *= this.friction;
    this.vy *= this.friction;

    // Keep within canvas bounds
    if (this.x < this.size / 2) {
      this.x = this.size / 2;
      this.vx *= -0.8; // Bounce off walls with energy loss
    } else if (this.x > width - this.size / 2) {
      this.x = width - this.size / 2;
      this.vx *= -0.8;
    }

    if (this.y < this.size / 2) {
      this.y = this.size / 2;
      this.vy *= -0.8;
    } else if (this.y > height - this.size / 2) {
      this.y = height - this.size / 2;
      this.vy *= -0.8;
    }
  }

  display() {
    // Add a subtle shadow effect based on velocity
    let speed = sqrt(this.vx * this.vx + this.vy * this.vy);
    let shadowOffset = map(speed, 0, 10, 0, 5);

    // Shadow
    noStroke();
    fill(0, 0, 0, 20);
    ellipse(this.x + shadowOffset, this.y + shadowOffset, this.size);

    // Circle
    noStroke();
    fill(this.color);
    ellipse(this.x, this.y, this.size);
  }
}

class SpecialCircle extends Circle {
  constructor(x, y, size, borderColor) {
    super(x, y, size, color(0, 0, 0, 0));
    this.borderColor = borderColor;
    this.borderWeight = 4;
    this.maxForce = 2;
  }

  update() {
    // The special circle follows the mouse position with easing
    if (mouseIsPressed) {
      this.x = mouseX;
      this.y = mouseY;
    } else {
      // Stay in center if mouse isn't pressed
      this.x = lerp(this.x, centerX, 0.02);
      this.y = lerp(this.y, centerY, 0.02);
    }
  }

  display() {
    // Draw transparent circle with colored border
    noFill();
    stroke(this.borderColor);
    strokeWeight(this.borderWeight);
    ellipse(this.x, this.y, this.size);

    // Add a subtle glow effect
    for (let i = 3; i > 0; i--) {
      stroke(red(this.borderColor), green(this.borderColor), blue(this.borderColor), 20 / i);
      strokeWeight(this.borderWeight + i * 3);
      ellipse(this.x, this.y, this.size);
    }
  }
}

// Resize canvas when window is resized
function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  centerX = width / 2;
  centerY = height / 2;
}