import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("AgriChainModule", (m) => {
  const AgriChain = m.contract("AgriChain");

  //m.call(counter, "incBy", [5n]);

  return { AgriChain };
});
