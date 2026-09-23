// Chair44 red/green edge-fold mechanism coupon, dimensions in millimetres.
// This curved relief and its hardware have NOT been validated as a tiling tile.
// Select part = "assembly", "body", "rotor", or "pin". STL exports use Y as
// their local print Z; set print_orientation=true for the same orientation.
part = "assembly";
print_orientation = false;
angle = 45;
side = 40;
radius = 10;
radial_clearance = 0.30;
rotor_width = 16;
axial_clearance = 0.30;
pin_diameter = 2;
body_bore = 2.2;
rotor_bore = 2.4;
rotor_hub_radius = 2.5;
body_hub_radius = 3.5;
hub_length = 2;
bearing_length = 3;
$fn = 128;
start = (side-rotor_width)/2;
end = start+rotor_width;
module along_y(r,a,b) { translate([0,a,0]) rotate([-90,0,0]) cylinder(r=r,h=b-a); }
module quadrant(r,a,b) {
 intersection() {
  along_y(r,a,b);
  translate([-r,a,-r]) cube([r,b-a,r]);
 }
}
module body() {
 difference() {
  union() {
   translate([-side,0,-side]) cube([side,side,side]);
   along_y(body_hub_radius,0,bearing_length);
   along_y(body_hub_radius,side-bearing_length,side);
  }
  along_y(radius+radial_clearance,start-axial_clearance,end+axial_clearance);
  along_y(body_bore/2,-1,side+1);
 }
}
module rotor() {
 difference() {
  union() {
   quadrant(radius,start,end);
   along_y(rotor_hub_radius,start,start+hub_length);
   along_y(rotor_hub_radius,end-hub_length,end);
  }
  along_y(rotor_bore/2,start-1,end+1);
 }
}
module pin() { along_y(pin_diameter/2,-2,side+2); }
module selected() {
 if(part=="body") body();
 else if(part=="rotor") rotor();
 else if(part=="pin") pin();
 else {
  color([.7,.8,.72,.4]) body();
  color([.8,.3,.25]) rotate([0,-angle,0]) rotor();
  color([.78,.6,.24]) pin();
 }
}
if(print_orientation && part!="assembly")
 rotate([90,0,0]) translate([0,part=="rotor"?-start:part=="pin"?2:0,0]) selected();
else selected();
